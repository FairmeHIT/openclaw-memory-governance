#!/usr/bin/env python3

import argparse
import json
import re
import time
from collections import Counter
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


def load_jsonl(path: Path) -> List[Dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def score(query: str, text: str) -> int:
    query_terms = Counter(tokenize(query))
    text_terms = Counter(tokenize(text))
    return sum(min(query_terms[token], text_terms[token]) for token in query_terms)


def decide(query: Dict, item: Dict) -> Tuple[str, str]:
    purpose = query["purpose"]
    requester_domain = WORKSPACE_DOMAIN.get(query["workspace"], query["workspace"].replace("workspace-", ""))

    if purpose == "external_share":
        if item["privacy_level"] in {"L2", "L3"}:
            return "deny", "external_high_sensitive"

    if item["domain"] not in {requester_domain, "shared"}:
        return "deny", "cross_domain"

    if item["lifecycle"] == "pending_delete":
        return "deny", "pending_delete"

    if item["privacy_level"] == "L3":
        if "sandbox_only" in item["purpose_allow"]:
            return "sandbox", "sandbox_only"
        return "deny", "l3_blocked"

    if item["privacy_level"] == "L2":
        return "downgrade", "l2_summary_default"

    if purpose in item["purpose_allow"] or item["privacy_level"] in {"L0", "L1"}:
        return "allow", "purpose_allowed"

    return "deny", "purpose_not_allowed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Guard retrieval against governed OpenClaw memory.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--queries", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    dataset = {item.get("chunk_id", item["memory_id"]): item for item in load_jsonl(Path(args.dataset))}
    queries = load_jsonl(Path(args.queries))
    run_dir = Path(args.run_dir)

    policy_rows = []
    retrieval_rows = []
    audit_rows = []
    sandbox_rows = []

    for query in queries:
        ranked = []
        for item_id, item in dataset.items():
            text = item.get("retrieval_text") or item.get("raw_text") or item.get("text", "")
            match_score = score(query["query"], text)
            if match_score > 0:
                ranked.append((match_score, item_id, item))
        ranked.sort(key=lambda x: (-x[0], x[1]))
        candidates = [row[2] for row in ranked[: args.top_k]]

        start = time.perf_counter()
        allowed, denied, downgraded, sandboxed = [], [], [], []
        deny_reasons = {}
        for item in candidates:
            item_id = item.get("chunk_id", item["memory_id"])
            decision, reason = decide(query, item)
            if decision == "allow":
                allowed.append(item)
            elif decision == "deny":
                denied.append(item)
                deny_reasons[item_id] = reason
            elif decision == "downgrade":
                downgraded.append(item)
                deny_reasons[item_id] = reason
            else:
                sandboxed.append(item)
                deny_reasons[item_id] = reason
        latency_ms = round((time.perf_counter() - start) * 1000, 3)

        policy_rows.append(
            {
                "query_id": query["query_id"],
                "agent_id": query["agent_id"],
                "workspace": query["workspace"],
                "purpose": query["purpose"],
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
                "query_id": query["query_id"],
                "returned_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in returned],
                "returned_domains": [item["domain"] for item in returned],
                "returned_privacy_levels": [item["privacy_level"] for item in returned],
                "raw_exposure": any(item["privacy_level"] in {"L2", "L3"} for item in allowed),
                "downgraded_summary_ids": [item.get("chunk_id", item["memory_id"]) for item in downgraded],
            }
        )

        for event_type, items in [("retrieval_allow", allowed), ("retrieval_deny", denied), ("retrieval_downgrade", downgraded), ("retrieval_sandbox", sandboxed)]:
            for item in items:
                item_id = item.get("chunk_id", item["memory_id"])
                audit_rows.append(
                    {
                        "event_type": event_type,
                        "query_id": query["query_id"],
                        "agent_id": query["agent_id"],
                        "chunk_id": item_id,
                        "domain": item["domain"],
                        "privacy_level": item["privacy_level"],
                        "purpose": query["purpose"],
                        "decision": event_type.replace("retrieval_", ""),
                        "reason": deny_reasons.get(item_id, "policy_allowed"),
                    }
                )
                if event_type == "retrieval_sandbox":
                    sandbox_rows.append(
                        {
                            "job_id": f"{query['query_id']}_{item_id}",
                            "request_id": query["query_id"],
                            "agent_id": query["agent_id"],
                            "input_privacy_levels": [item["privacy_level"]],
                            "output_mode": "summary_only",
                            "raw_output_blocked": True,
                            "status": "queued",
                            "latency_ms": None,
                        }
                    )

    write_jsonl(run_dir / "policy_decisions.jsonl", policy_rows)
    write_jsonl(run_dir / "retrieval_hits.jsonl", retrieval_rows)
    write_jsonl(run_dir / "audit_events.jsonl", audit_rows)
    write_jsonl(run_dir / "sandbox_jobs.jsonl", sandbox_rows)
    print(f"Wrote guarded retrieval logs to {run_dir}")


if __name__ == "__main__":
    main()
