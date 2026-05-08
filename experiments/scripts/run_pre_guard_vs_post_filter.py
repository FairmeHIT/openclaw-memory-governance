#!/usr/bin/env python3

import argparse
import json
import re
import sqlite3
import time
from collections import Counter
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
MODES = ["baseline_raw", "post_filter", "pre_guard"]


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


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_governance(db_path: Path) -> Dict[str, Dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM memory_governance").fetchall()
    finally:
        conn.close()
    governance = {}
    for row in rows:
        item = dict(row)
        item["purpose_allow"] = json.loads(item["purpose_allow"])
        governance[item["chunk_id"]] = item
    return governance


def item_id(item: Dict) -> str:
    return item.get("chunk_id", item["memory_id"])


def rank(level: str) -> int:
    return PRIVACY_RANK.get(level, 0)


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


def unauthorized_for_query(query: Dict, item: Dict) -> bool:
    expected_domains = set(query.get("expected_domains") or [])
    if not expected_domains:
        return True
    if item["domain"] not in expected_domains | {"shared"}:
        return True
    expected_rank = rank(query.get("expected_max_privacy", "L3"))
    return rank(item["privacy_level"]) > expected_rank


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


def run_baseline(query: Dict, ranked: List[Dict], top_k: int) -> Tuple[List[Dict], List[Dict], float]:
    start = time.perf_counter()
    selected = ranked[:top_k]
    latency = round((time.perf_counter() - start) * 1000, 3)
    return selected, selected, latency


def run_post_filter(
    query: Dict,
    ranked: List[Dict],
    governance: Dict[str, Dict],
    top_k: int,
) -> Tuple[List[Dict], List[Dict], float]:
    start = time.perf_counter()
    raw_boundary = ranked[:top_k]
    returned = []
    for item in raw_boundary:
        decision, _ = decide(query, item, governance[item_id(item)])
        if decision in {"allow", "downgrade"}:
            returned.append(item)
    latency = round((time.perf_counter() - start) * 1000, 3)
    return raw_boundary, returned, latency


def run_pre_guard(
    query: Dict,
    ranked: List[Dict],
    governance: Dict[str, Dict],
    top_k: int,
) -> Tuple[List[Dict], List[Dict], float]:
    start = time.perf_counter()
    returned = []
    raw_boundary = []
    for item in ranked:
        decision, _ = decide(query, item, governance[item_id(item)])
        if decision == "allow":
            returned.append(item)
            raw_boundary.append(item)
        elif decision == "downgrade":
            returned.append(item)
        if len(returned) >= top_k:
            break
    latency = round((time.perf_counter() - start) * 1000, 3)
    return raw_boundary, returned, latency


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare baseline raw retrieval, post-filtering, and pre-return memory guarding."
    )
    parser.add_argument("--dataset", default="experiments/datasets/real_memory_chunks.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/real_chunk_query_set.jsonl")
    parser.add_argument("--db", default="experiments/governance_real_chunks.sqlite")
    parser.add_argument("--run-id", default="pre_guard_vs_post_filter_v1")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    dataset = load_jsonl(Path(args.dataset))
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
                raw_boundary, returned, latency = run_baseline(query, ranked, args.top_k)
            elif mode == "post_filter":
                raw_boundary, returned, latency = run_post_filter(query, ranked, governance, args.top_k)
            else:
                raw_boundary, returned, latency = run_pre_guard(query, ranked, governance, args.top_k)

            detail_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "mode": mode,
                    "query_id": query["query_id"],
                    "purpose": query["purpose"],
                    "workspace": query["workspace"],
                    "raw_boundary_chunk_ids": [item_id(item) for item in raw_boundary],
                    "returned_chunk_ids": [item_id(item) for item in returned],
                    "raw_boundary_sensitive": any(sensitive(item) for item in raw_boundary),
                    "raw_boundary_unauthorized": any(unauthorized_for_query(query, item) for item in raw_boundary),
                    "returned_unauthorized": any(unauthorized_for_query(query, item) for item in returned),
                    "sensitive_raw_exposure": any(sensitive(item) for item in raw_boundary),
                    "task_success": bool(returned),
                    "returned_count": len(returned),
                    "policy_eval_latency_ms": latency,
                }
            )

    metrics = {"run_id": args.run_id, "modes": {}}
    for mode in MODES:
        rows = [row for row in detail_rows if row["mode"] == mode]
        count = len(rows) or 1
        latencies = [row["policy_eval_latency_ms"] for row in rows]
        metrics["modes"][mode] = {
            "task_success_rate": round(sum(1 for row in rows if row["task_success"]) / count, 4),
            "raw_boundary_exposure_rate": round(
                sum(1 for row in rows if row["raw_boundary_sensitive"] or row["raw_boundary_unauthorized"]) / count,
                4,
            ),
            "returned_unauthorized_rate": round(
                sum(1 for row in rows if row["returned_unauthorized"]) / count,
                4,
            ),
            "sensitive_raw_exposure_rate": round(
                sum(1 for row in rows if row["sensitive_raw_exposure"]) / count,
                4,
            ),
            "avg_returned_count": round(sum(row["returned_count"] for row in rows) / count, 4),
            "policy_eval_latency_ms_p50": round(median(latencies), 3) if latencies else 0.0,
        }

    write_jsonl(run_dir / "details.jsonl", detail_rows)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
