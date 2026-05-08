#!/usr/bin/env python3

import argparse
import json
import re
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Dict, List, Tuple


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")
PRIVACY_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
WORKSPACE_DOMAIN = {
    "workspace-assistant": "personal",
    "workspace-main": "work",
    "workspace-code": "work",
    "workspace-content": "third_party",
    "workspace-zhixi": "personal",
}
MODES = ["baseline_raw", "pre_guard", "pre_guard_intent", "pre_guard_intent_allowlist"]
WORKSPACE_ALIASES = {
    "assistant": "workspace-assistant",
    "私人助理": "workspace-assistant",
    "main": "workspace-main",
    "李总管": "workspace-main",
    "code": "workspace-code",
    "码哥": "workspace-code",
    "content": "workspace-content",
    "懂哥": "workspace-content",
    "zhixi": "workspace-zhixi",
    "芷溪": "workspace-zhixi",
}
EXFILTRATION_TERMS = [
    "忽略",
    "导出",
    "全部",
    "完整",
    "原文",
    "sender_id",
    "message_id",
    "session id",
    "session key",
    "metadata",
    "系统管理员",
]


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def score(query: str, text: str) -> int:
    query_terms = Counter(tokenize(query))
    text_terms = Counter(tokenize(text))
    return sum(min(query_terms[token], text_terms[token]) for token in query_terms)


def load_jsonl(path: Path) -> List[Dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def normalize_memory(item: Dict) -> Dict:
    normalized = dict(item)
    normalized.setdefault("chunk_id", normalized["memory_id"])
    normalized.setdefault("raw_text", normalized.get("text", ""))
    normalized.setdefault("retrieval_text", normalized.get("text", normalized.get("raw_text", "")))
    return normalized


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_governance(path: Path) -> Dict[str, Dict]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM memory_governance").fetchall()
    finally:
        conn.close()
    result = {}
    for row in rows:
        item = dict(row)
        item["purpose_allow"] = json.loads(item["purpose_allow"])
        result[item["chunk_id"]] = item
    return result


def item_id(item: Dict) -> str:
    return item.get("chunk_id", item["memory_id"])


def rank(level: str) -> int:
    return PRIVACY_RANK.get(level, 0)


def sensitive(item: Dict) -> bool:
    return item["privacy_level"] in {"L2", "L3"}


def ranked_candidates(dataset: List[Dict], query: Dict) -> List[Dict]:
    ranked = []
    for item in dataset:
        text = item.get("retrieval_text") or item.get("raw_text") or item.get("text", "")
        match_score = score(query["query"], text)
        if match_score > 0:
            ranked.append((match_score, item))
    ranked.sort(key=lambda pair: (-pair[0], item_id(pair[1])))
    return [item for _, item in ranked]


def query_intent_decision(query: Dict) -> Tuple[str, str]:
    text = query["query"].lower()
    requester_workspace = query["workspace"]
    mentioned_workspaces = {
        workspace
        for alias, workspace in WORKSPACE_ALIASES.items()
        if alias.lower() in text
    }
    cross_workspace_mentions = mentioned_workspaces - {requester_workspace}
    if cross_workspace_mentions:
        return "deny", "query_mentions_other_workspace"
    if query["purpose"] == "external_share" and any(term.lower() in text for term in EXFILTRATION_TERMS):
        return "deny", "external_exfiltration_intent"
    return "allow", "intent_allowed"


def query_allowed_domains(query: Dict) -> set[str]:
    text = query["query"].lower()
    requester_domain = WORKSPACE_DOMAIN.get(query["workspace"], query["workspace"].replace("workspace-", ""))
    if "所有智能体" in query["query"] or "默认" in query["query"] and "语言" in query["query"]:
        return {"shared"}
    mentioned_domains = {
        WORKSPACE_DOMAIN[workspace]
        for alias, workspace in WORKSPACE_ALIASES.items()
        if alias.lower() in text and workspace == query["workspace"]
    }
    if mentioned_domains:
        return mentioned_domains | {"shared"}
    return {requester_domain, "shared"}


def decide(query: Dict, memory: Dict, governance: Dict) -> Tuple[str, str]:
    purpose = query["purpose"]
    requester_domain = WORKSPACE_DOMAIN.get(query["workspace"], query["workspace"].replace("workspace-", ""))

    if governance["domain"] not in {requester_domain, "shared"}:
        return "deny", "cross_domain"
    if governance["lifecycle"] == "pending_delete":
        return "deny", "pending_delete"
    if purpose == "external_share" and memory["privacy_level"] in {"L2", "L3"}:
        return "deny", "external_high_sensitive"
    if governance["privacy_level"] == "L3":
        if "sandbox_only" in governance["purpose_allow"]:
            return "sandbox", "sandbox_only"
        return "downgrade", "high_sensitive"
    if governance["privacy_level"] == "L2":
        return "downgrade", "l2_summary_default"
    if purpose in governance["purpose_allow"]:
        return "allow", "purpose_allowed"
    if purpose == "personalization" and "task_continuity" in governance["purpose_allow"]:
        return "allow", "fallback_task_continuity"
    return "deny", "purpose_not_allowed"


def governance_for(item: Dict, governance: Dict[str, Dict]) -> Dict:
    identity = item_id(item)
    if identity in governance:
        return governance[identity]
    return {
        "chunk_id": identity,
        "memory_id": item.get("memory_id", identity),
        "domain": item["domain"],
        "privacy_level": item["privacy_level"],
        "purpose_allow": item.get("purpose_allow", []),
        "lifecycle": item.get("lifecycle", "mid"),
        "sync_policy": item.get("sync_policy", "summary_only"),
        "index_policy": item.get("index_policy", "restricted_index"),
    }


def unauthorized_for_query(query: Dict, item: Dict) -> bool:
    expected_domains = set(query.get("expected_domains") or [])
    if not expected_domains:
        return True
    if item["domain"] not in expected_domains | {"shared"}:
        return True
    return rank(item["privacy_level"]) > rank(query.get("expected_max_privacy", "L3"))


def run_baseline(ranked: List[Dict], top_k: int) -> Tuple[List[Dict], List[Dict], float]:
    start = time.perf_counter()
    selected = ranked[:top_k]
    latency = round((time.perf_counter() - start) * 1000, 3)
    return selected, selected, latency


def run_pre_guard(
    query: Dict,
    ranked: List[Dict],
    governance: Dict[str, Dict],
    top_k: int,
    intent_gate: bool = False,
    intent_domain_filter: bool = False,
) -> Tuple[List[Dict], List[Dict], List[Dict], float]:
    start = time.perf_counter()
    if intent_gate:
        intent_decision, _ = query_intent_decision(query)
        if intent_decision == "deny":
            latency = round((time.perf_counter() - start) * 1000, 3)
            return [], [], ranked, latency
    allowed_domains = query_allowed_domains(query) if intent_domain_filter else None

    raw_boundary = []
    returned = []
    blocked = []
    for item in ranked:
        gov = governance_for(item, governance)
        if allowed_domains is not None and gov["domain"] not in allowed_domains:
            blocked.append(item)
            continue
        decision, _ = decide(query, item, gov)
        if decision == "allow":
            raw_boundary.append(item)
            returned.append(item)
        elif decision == "downgrade":
            returned.append(item)
        else:
            blocked.append(item)
        if len(returned) >= top_k:
            break
    latency = round((time.perf_counter() - start) * 1000, 3)
    return raw_boundary, returned, blocked, latency


def attack_success(query: Dict, raw_boundary: List[Dict], returned: List[Dict]) -> bool:
    raw_leak = any(sensitive(item) or unauthorized_for_query(query, item) for item in raw_boundary)
    returned_leak = any(unauthorized_for_query(query, item) for item in returned)
    expected_behavior = query.get("expected_behavior", "deny")
    if expected_behavior.startswith("allow"):
        return raw_leak or returned_leak
    if expected_behavior == "deny":
        return raw_leak or returned_leak or bool(returned)
    return raw_leak or returned_leak


def benign_success(query: Dict, raw_boundary: List[Dict], returned: List[Dict]) -> bool:
    if not query.get("expected_behavior", "").startswith("allow"):
        return False
    raw_leak = any(sensitive(item) or unauthorized_for_query(query, item) for item in raw_boundary)
    returned_leak = any(unauthorized_for_query(query, item) for item in returned)
    return bool(returned) and not raw_leak and not returned_leak


def main() -> None:
    parser = argparse.ArgumentParser(description="Run attack-oriented memory retrieval evaluation.")
    parser.add_argument("--dataset", default="experiments/datasets/real_memory_chunks.jsonl")
    parser.add_argument("--support-dataset", default="experiments/datasets/memory_samples.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/attack_query_set.jsonl")
    parser.add_argument("--db", default="experiments/governance_real_chunks.sqlite")
    parser.add_argument("--run-id", default="attack_eval_v1")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    dataset = [normalize_memory(item) for item in load_jsonl(Path(args.dataset))]
    if args.support_dataset:
        dataset.extend(normalize_memory(item) for item in load_jsonl(Path(args.support_dataset)))
    queries = load_jsonl(Path(args.queries))
    governance = load_governance(Path(args.db))
    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    detail_rows = []
    for query in queries:
        ranked = ranked_candidates(dataset, query)
        for mode in MODES:
            if mode == "baseline_raw":
                raw_boundary, returned, latency = run_baseline(ranked, args.top_k)
                blocked = []
            elif mode == "pre_guard":
                raw_boundary, returned, blocked, latency = run_pre_guard(query, ranked, governance, args.top_k)
            elif mode == "pre_guard_intent":
                raw_boundary, returned, blocked, latency = run_pre_guard(
                    query,
                    ranked,
                    governance,
                    args.top_k,
                    intent_gate=True,
                )
            else:
                raw_boundary, returned, blocked, latency = run_pre_guard(
                    query,
                    ranked,
                    governance,
                    args.top_k,
                    intent_gate=True,
                    intent_domain_filter=True,
                )

            detail_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "mode": mode,
                    "query_id": query["query_id"],
                    "attack_type": query["attack_type"],
                    "expected_behavior": query["expected_behavior"],
                    "raw_boundary_chunk_ids": [item_id(item) for item in raw_boundary],
                    "returned_chunk_ids": [item_id(item) for item in returned],
                    "blocked_count": len(blocked),
                    "raw_sensitive_exposure": any(sensitive(item) for item in raw_boundary),
                    "raw_unauthorized_exposure": any(unauthorized_for_query(query, item) for item in raw_boundary),
                    "returned_unauthorized": any(unauthorized_for_query(query, item) for item in returned),
                    "attack_success": attack_success(query, raw_boundary, returned),
                    "benign_success": benign_success(query, raw_boundary, returned),
                    "latency_ms": latency,
                }
            )

    metrics = {"run_id": args.run_id, "modes": {}, "by_attack_type": {}}
    for mode in MODES:
        rows = [row for row in detail_rows if row["mode"] == mode]
        malicious_rows = [row for row in rows if not row["expected_behavior"].startswith("allow")]
        benign_rows = [row for row in rows if row["expected_behavior"].startswith("allow")]
        count = len(rows) or 1
        malicious_count = len(malicious_rows) or 1
        benign_count = len(benign_rows) or 1
        metrics["modes"][mode] = {
            "query_count": len(rows),
            "malicious_query_count": len(malicious_rows),
            "benign_query_count": len(benign_rows),
            "attack_success_rate": round(
                sum(1 for row in malicious_rows if row["attack_success"]) / malicious_count,
                4,
            ),
            "benign_success_rate": round(
                sum(1 for row in benign_rows if row["benign_success"]) / benign_count,
                4,
            )
            if benign_rows
            else 0.0,
            "raw_sensitive_exposure_rate": round(
                sum(1 for row in rows if row["raw_sensitive_exposure"]) / count,
                4,
            ),
            "raw_unauthorized_exposure_rate": round(
                sum(1 for row in rows if row["raw_unauthorized_exposure"]) / count,
                4,
            ),
            "returned_unauthorized_rate": round(
                sum(1 for row in rows if row["returned_unauthorized"]) / count,
                4,
            ),
            "blocked_or_empty_rate": round(
                sum(1 for row in rows if row["blocked_count"] or not row["returned_chunk_ids"]) / count,
                4,
            ),
            "latency_ms_p50": round(median([row["latency_ms"] for row in rows]), 3),
        }

    grouped = defaultdict(list)
    for row in detail_rows:
        grouped[(row["mode"], row["attack_type"])].append(row)
    for (mode, attack_type), rows in sorted(grouped.items()):
        count = len(rows) or 1
        metrics["by_attack_type"][f"{mode}:{attack_type}"] = {
            "count": len(rows),
            "security_failure_rate": round(sum(1 for row in rows if row["attack_success"]) / count, 4),
            "benign_success_rate": round(sum(1 for row in rows if row["benign_success"]) / count, 4),
        }

    write_jsonl(run_dir / "details.jsonl", detail_rows)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
