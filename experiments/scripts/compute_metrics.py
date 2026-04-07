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

    if policy_rows:
        policy_enforcement = sum(
            1
            for row in policy_rows
            if row["denied_chunk_ids"] or row["downgraded_chunk_ids"] or row["sandbox_chunk_ids"]
        )

    latencies = [row["policy_eval_latency_ms"] for row in policy_rows]
    metrics = {
        "run_id": args.run_id,
        "task_success_rate": round(task_success / total_queries, 4) if total_queries else 0.0,
        "unauthorized_recall_rate": round(unauthorized_recall / total_queries, 4) if total_queries else 0.0,
        "sensitive_raw_exposure_rate": round(sensitive_raw_exposure / total_queries, 4) if total_queries else 0.0,
        "cross_domain_leak_count": cross_domain_leak_count,
        "policy_enforcement_rate": round(policy_enforcement / total_queries, 4) if total_queries else 0.0,
        "policy_eval_latency_ms_p50": round(median(latencies), 3) if latencies else 0.0,
        "policy_eval_latency_ms_p95": percentile(latencies, 0.95),
    }

    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
