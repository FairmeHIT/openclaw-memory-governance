#!/usr/bin/env python3

import argparse
import json
import re
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")
WORKSPACE_DOMAIN = {
    "workspace-assistant": "personal",
    "workspace-main": "work",
    "workspace-code": "work",
    "workspace-content": "third_party",
    "workspace-zhixi": "personal",
}


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def score(query: str, text: str) -> int:
    query_terms = Counter(tokenize(query))
    text_terms = Counter(tokenize(text))
    return sum(min(query_terms[token], text_terms[token]) for token in query_terms)


def load_jsonl(path: str) -> List[Dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_governance(db_path: str) -> Dict[str, Dict]:
    conn = sqlite3.connect(db_path)
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


def decide(query: Dict, memory: Dict, governance: Dict, policy_mode: str) -> Tuple[str, str]:
    purpose = query["purpose"]
    requester_domain = WORKSPACE_DOMAIN.get(query["workspace"], query["workspace"].replace("workspace-", ""))

    if governance["domain"] not in {requester_domain, "shared"}:
        return "deny", "cross_domain"

    if governance["lifecycle"] == "pending_delete":
        return "deny", "pending_delete"

    if policy_mode == "light":
        if purpose == "external_share" and memory["privacy_level"] == "L3":
            return "deny", "external_l3_only"
        if purpose in governance["purpose_allow"]:
            return "allow", "light_purpose_allowed"
        if purpose == "personalization" and "task_continuity" in governance["purpose_allow"]:
            return "allow", "light_fallback_task_continuity"
        return "allow", "light_default_allow"

    if purpose == "external_share":
        if memory["privacy_level"] in {"L2", "L3"}:
            return "deny", "external_high_sensitive"
        if "summary_only" in governance["purpose_allow"]:
            return "downgrade", "summary_only"
        if "deny_external" in governance["purpose_allow"]:
            return "deny", "deny_external"

    if governance["privacy_level"] == "L3":
        if "sandbox_only" in governance["purpose_allow"]:
            return "sandbox", "sandbox_only"
        return "downgrade", "high_sensitive"

    if governance["privacy_level"] == "L2":
        if purpose == "external_share":
            return "downgrade", "summary_only"
        return "downgrade", "l2_summary_default"

    if purpose in governance["purpose_allow"]:
        return "allow", "purpose_allowed"

    if purpose == "personalization" and "task_continuity" in governance["purpose_allow"]:
        return "allow", "fallback_task_continuity"

    return "deny", "purpose_not_allowed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run guarded retrieval with governance filtering.")
    parser.add_argument("--dataset", default="experiments/datasets/memory_samples.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/query_set.jsonl")
    parser.add_argument("--db", default="experiments/governance.sqlite")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--policy-mode", choices=["full", "light"], default="full")
    args = parser.parse_args()

    dataset = {
        item.get("chunk_id", item["memory_id"]): item
        for item in load_jsonl(args.dataset)
    }
    queries = load_jsonl(args.queries)
    governance = load_governance(args.db)
    run_dir = Path("experiments/runs") / args.run_id
    ts = datetime.now(timezone.utc).isoformat()

    policy_rows = []
    retrieval_rows = []
    audit_rows = []
    sandbox_rows = []
    exposure_rows = []

    for query in queries:
        retrieval_start = time.perf_counter()
        ranked = []
        for memory in dataset.values():
            memory_text = memory.get("retrieval_text") or memory.get("raw_text") or memory.get("text", "")
            match_score = score(query["query"], memory_text)
            if match_score > 0:
                ranked.append((match_score, memory))
        ranked.sort(key=lambda item: (-item[0], item[1]["memory_id"]))
        candidates = [item[1] for item in ranked[: args.top_k]]

        start = time.perf_counter()
        allowed = []
        denied = []
        downgraded = []
        sandboxed = []
        deny_reasons = {}

        for item in candidates:
            item_id = item.get("chunk_id", item["memory_id"])
            gov = governance[item_id]
            decision, reason = decide(query, item, gov, args.policy_mode)
            if decision == "allow":
                allowed.append(item)
            elif decision == "deny":
                denied.append(item)
                deny_reasons[item_id] = reason
            elif decision == "downgrade":
                downgraded.append(item)
                deny_reasons[item_id] = reason
            elif decision == "sandbox":
                sandboxed.append(item)
                deny_reasons[item_id] = reason
        latency_ms = round((time.perf_counter() - start) * 1000, 3)

        policy_rows.append(
            {
                "ts": ts,
                "run_id": args.run_id,
                "query_id": query["query_id"],
                "agent_id": query["agent_id"],
                "workspace": query["workspace"],
                "purpose": query["purpose"],
                "policy_mode": args.policy_mode,
                "candidate_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in candidates],
                "allowed_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in allowed],
                "denied_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in denied],
                "downgraded_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in downgraded],
                "sandbox_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in sandboxed],
                "deny_reasons": deny_reasons,
                "policy_eval_latency_ms": latency_ms,
            }
        )

        returned = allowed + downgraded
        retrieval_rows.append(
            {
                "ts": ts,
                "run_id": args.run_id,
                "query_id": query["query_id"],
                "policy_mode": args.policy_mode,
                "candidate_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in candidates],
                "returned_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in returned],
                "returned_domains": [item["domain"] for item in returned],
                "returned_privacy_levels": [item["privacy_level"] for item in returned],
                "raw_exposure": any(item["privacy_level"] in {"L2", "L3"} for item in allowed),
                "downgraded_summary_ids": [item.get("chunk_id", item["memory_id"]) for item in downgraded],
                "retrieval_latency_ms": round((time.perf_counter() - retrieval_start) * 1000, 3),
                "answer_text": " ".join(
                    ((item.get("retrieval_text") or item.get("raw_text") or item.get("text") or "").strip())
                    for item in allowed
                ).strip() or None,
                "summary_text": " ".join(
                    ((item.get("retrieval_text") or item.get("raw_text") or item.get("text") or "").strip())
                    for item in downgraded
                ).strip() or None,
            }
        )

        for item in allowed:
            chunk_id = item.get("chunk_id", item["memory_id"])
            audit_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "event_type": "retrieval_allow",
                    "query_id": query["query_id"],
                    "agent_id": query["agent_id"],
                    "chunk_id": chunk_id,
                    "domain": item["domain"],
                    "privacy_level": item["privacy_level"],
                    "purpose": query["purpose"],
                    "decision": "allow",
                    "reason": "policy_allowed",
                }
            )
            if item["privacy_level"] in {"L2", "L3"}:
                exposure_rows.append(
                    {
                        "ts": ts,
                        "run_id": args.run_id,
                        "query_id": query["query_id"],
                        "agent_id": query["agent_id"],
                        "chunk_id": chunk_id,
                        "privacy_level": item["privacy_level"],
                        "domain": item["domain"],
                        "exposure_mode": "raw",
                        "decision": "allow",
                    }
                )
        for item in denied:
            audit_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "event_type": "retrieval_deny",
                    "query_id": query["query_id"],
                    "agent_id": query["agent_id"],
                    "chunk_id": item.get("chunk_id", item["memory_id"]),
                    "domain": item["domain"],
                    "privacy_level": item["privacy_level"],
                    "purpose": query["purpose"],
                    "decision": "deny",
                    "reason": deny_reasons[item.get("chunk_id", item["memory_id"])],
                }
            )
        for item in downgraded:
            chunk_id = item.get("chunk_id", item["memory_id"])
            audit_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "event_type": "retrieval_downgrade",
                    "query_id": query["query_id"],
                    "agent_id": query["agent_id"],
                    "chunk_id": chunk_id,
                    "domain": item["domain"],
                    "privacy_level": item["privacy_level"],
                    "purpose": query["purpose"],
                    "decision": "downgrade",
                    "reason": deny_reasons[chunk_id],
                }
            )
            exposure_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "query_id": query["query_id"],
                    "agent_id": query["agent_id"],
                    "chunk_id": chunk_id,
                    "privacy_level": item["privacy_level"],
                    "domain": item["domain"],
                    "exposure_mode": "summary",
                    "decision": "downgrade",
                }
            )
        for item in sandboxed:
            chunk_id = item.get("chunk_id", item["memory_id"])
            sandbox_rows.append(
                {
                    "ts": ts,
                    "job_id": f"{args.run_id}_{query['query_id']}_{chunk_id}",
                    "request_id": query["query_id"],
                    "agent_id": query["agent_id"],
                    "input_privacy_levels": [item["privacy_level"]],
                    "output_mode": "summary_only",
                    "raw_output_blocked": True,
                    "status": "queued",
                    "latency_ms": None,
                }
            )
            audit_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "event_type": "retrieval_sandbox",
                    "query_id": query["query_id"],
                    "agent_id": query["agent_id"],
                    "chunk_id": chunk_id,
                    "domain": item["domain"],
                    "privacy_level": item["privacy_level"],
                    "purpose": query["purpose"],
                    "decision": "sandbox",
                    "reason": deny_reasons[chunk_id],
                }
            )
            exposure_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "query_id": query["query_id"],
                    "agent_id": query["agent_id"],
                    "chunk_id": chunk_id,
                    "privacy_level": item["privacy_level"],
                    "domain": item["domain"],
                    "exposure_mode": "sandbox",
                    "decision": "sandbox",
                }
            )

    write_jsonl(run_dir / "policy_decisions.jsonl", policy_rows)
    write_jsonl(run_dir / "retrieval_hits.jsonl", retrieval_rows)
    write_jsonl(run_dir / "audit_events.jsonl", audit_rows)
    write_jsonl(run_dir / "sandbox_jobs.jsonl", sandbox_rows)
    write_jsonl(run_dir / "exposures.jsonl", exposure_rows)
    print(f"Guarded run completed: {run_dir}")


if __name__ == "__main__":
    main()
