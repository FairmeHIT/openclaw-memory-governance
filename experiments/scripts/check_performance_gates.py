#!/usr/bin/env python3

import argparse
import json
import shutil
from pathlib import Path
from typing import Dict


MAX_GUARDED_RETRIEVAL_OVERHEAD_MS = 1.0
MAX_POLICY_EVAL_P50_MS = 1.0
MAX_SANDBOX_OVERHEAD_P50_MS = 10.0
MAX_ENCRYPTED_PAYLOAD_BYTES = 2048


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mode(metrics: Dict, name: str) -> Dict:
    return metrics.get("modes", {}).get(name, {})


def evaluate_gates(metrics: Dict) -> Dict[str, bool]:
    overhead = metrics["real_chunk_guarded_retrieval_p50"] - metrics["real_chunk_baseline_retrieval_p50"]
    return {
        "guarded_retrieval_overhead_within_budget": overhead <= MAX_GUARDED_RETRIEVAL_OVERHEAD_MS,
        "policy_eval_within_budget": metrics["real_chunk_guarded_policy_eval_p50"] <= MAX_POLICY_EVAL_P50_MS,
        "sandbox_overhead_within_budget": metrics["sandbox_job_overhead_p50"] <= MAX_SANDBOX_OVERHEAD_P50_MS,
        "encrypted_payload_within_budget": metrics["encryption_payload_bytes"] <= MAX_ENCRYPTED_PAYLOAD_BYTES,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check bounded prototype latency and artifact-size acceptance gates.")
    parser.add_argument("--run-id", default="performance_gates_v1")
    args = parser.parse_args()

    run_root = Path("experiments/runs")
    baseline = load_json(run_root / "real_chunk_baseline_v1/metrics.json")
    guarded = load_json(run_root / "real_chunk_guarded_v2/metrics.json")
    sandbox = load_json(run_root / "sandbox_eval_v1/metrics.json")
    encryption = load_json(run_root / "encryption_eval_v1/metrics.json")
    metrics = {
        "real_chunk_baseline_retrieval_p50": baseline["retrieval_latency_ms_p50"],
        "real_chunk_guarded_retrieval_p50": guarded["retrieval_latency_ms_p50"],
        "real_chunk_guarded_policy_eval_p50": guarded["policy_eval_latency_ms_p50"],
        "sandbox_job_overhead_p50": mode(sandbox, "sandbox_job")["sandbox_overhead_ms_p50"],
        "encryption_payload_bytes": encryption["encrypted_payload_bytes"],
    }
    gates = evaluate_gates(metrics)
    result = {
        "run_id": args.run_id,
        "metrics": metrics,
        "guarded_retrieval_overhead_p50_ms": round(
            metrics["real_chunk_guarded_retrieval_p50"] - metrics["real_chunk_baseline_retrieval_p50"],
            3,
        ),
        "gates": gates,
        "all_gates_passed": all(gates.values()),
    }
    run_dir = run_root / args.run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
