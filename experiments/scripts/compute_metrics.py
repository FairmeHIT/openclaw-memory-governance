#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from statistics import median
from typing import Dict, List


PRIVACY_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}


def load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def keyword_hits(text: str, keywords: List[str]) -> int:
    if not text:
        return 0
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lower)


def percentile(values: List[float], ratio: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = min(len(values) - 1, int((len(values) - 1) * ratio))
    return round(values[idx], 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute experiment metrics from run logs.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--queries", default="experiments/datasets/query_set.jsonl")
    args = parser.parse_args()

    run_dir = Path("experiments/runs") / args.run_id
    retrieval_rows = load_jsonl(run_dir / "retrieval_hits.jsonl")
    policy_rows = load_jsonl(run_dir / "policy_decisions.jsonl")
    audit_rows = load_jsonl(run_dir / "audit_events.jsonl")
    exposure_rows = load_jsonl(run_dir / "exposures.jsonl")
    sandbox_rows = load_jsonl(run_dir / "sandbox_jobs.jsonl")
    queries = {
        item["query_id"]: item
        for item in load_jsonl(Path(args.queries))
    }

    total_queries = len(queries)
    task_success = 0
    unauthorized_recall = 0
    sensitive_raw_exposure = 0
    cross_domain_leak_count = 0
    policy_enforcement = 0
    answer_quality_total = 0.0
    summary_utility_total = 0.0

    for row in retrieval_rows:
        query = queries[row["query_id"]]
        returned_domains = set(row["returned_domains"])
        returned_privacy_levels = row["returned_privacy_levels"]
        returned_max_privacy = max((PRIVACY_RANK[p] for p in returned_privacy_levels), default=0)
        expected_max = PRIVACY_RANK[query["expected_max_privacy"]]

        if row["returned_chunk_ids"]:
            task_success += 1

        expected_domains = set(query["expected_domains"])
        if expected_domains and not returned_domains.issubset(expected_domains | {"shared"}):
            cross_domain_leak_count += 1
            unauthorized_recall += 1

        if returned_max_privacy > expected_max:
            unauthorized_recall += 1

        if row["raw_exposure"]:
            sensitive_raw_exposure += 1

        answer_text = row.get("answer_text") or ""
        summary_text = row.get("summary_text") or ""
        expected_keywords = query.get("expected_keywords") or []
        utility_min = query.get("utility_min_keywords")
        if expected_keywords:
            keyword_score = keyword_hits(answer_text or summary_text, expected_keywords) / len(expected_keywords)
            answer_quality_total += keyword_score
            if summary_text:
                summary_utility_total += 1.0 if keyword_hits(summary_text, expected_keywords) >= (utility_min or 1) else 0.0
        else:
            expected_behavior = query.get("expected_behavior", "allow")
            if expected_behavior == "allow":
                answer_quality_total += 1.0 if row["returned_chunk_ids"] else 0.0
            elif expected_behavior in {"deny", "deny_or_summary"}:
                answer_quality_total += 1.0 if not row["raw_exposure"] else 0.0
            if summary_text:
                summary_utility_total += 1.0 if row["returned_chunk_ids"] else 0.0

    if policy_rows:
        policy_enforcement = sum(
            1
            for row in policy_rows
            if row["denied_chunk_ids"] or row["downgraded_chunk_ids"] or row["sandbox_chunk_ids"]
        )

    latencies = [row["policy_eval_latency_ms"] for row in policy_rows]
    retrieval_latencies = [row.get("retrieval_latency_ms", 0.0) for row in retrieval_rows if row.get("retrieval_latency_ms") is not None]
    expected_audit_events = 0
    for row in retrieval_rows:
        expected_audit_events += len(row.get("returned_chunk_ids", []))
    for row in policy_rows:
        expected_audit_events += len(row.get("denied_chunk_ids", [])) + len(row.get("sandbox_chunk_ids", []))

    sandbox_latencies = [row.get("latency_ms") for row in sandbox_rows if row.get("latency_ms") is not None]
    metrics = {
        "run_id": args.run_id,
        "task_success_rate": round(task_success / total_queries, 4) if total_queries else 0.0,
        "unauthorized_recall_rate": round(unauthorized_recall / total_queries, 4) if total_queries else 0.0,
        "sensitive_raw_exposure_rate": round(sensitive_raw_exposure / total_queries, 4) if total_queries else 0.0,
        "cross_domain_leak_count": cross_domain_leak_count,
        "policy_enforcement_rate": round(policy_enforcement / total_queries, 4) if total_queries else 0.0,
        "audit_completeness_rate": round(len(audit_rows) / expected_audit_events, 4) if expected_audit_events else 0.0,
        "answer_quality_score": round(answer_quality_total / total_queries, 4) if total_queries else 0.0,
        "summary_utility_score": round(summary_utility_total / total_queries, 4) if total_queries else 0.0,
        "retrieval_latency_ms_p50": round(median(retrieval_latencies), 3) if retrieval_latencies else 0.0,
        "retrieval_latency_ms_p95": percentile(retrieval_latencies, 0.95),
        "policy_eval_latency_ms_p50": round(median(latencies), 3) if latencies else 0.0,
        "policy_eval_latency_ms_p95": percentile(latencies, 0.95),
        "sandbox_overhead_ms_p50": round(median(sandbox_latencies), 3) if sandbox_latencies else 0.0,
        "sandbox_overhead_ms_p95": percentile(sandbox_latencies, 0.95),
        "exposure_event_count": len(exposure_rows),
    }

    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
