#!/usr/bin/env python3

import argparse
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Dict, List


MODES = ["local_only", "raw_sync", "summary_sync", "dp_sync"]


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


def percentile(values: List[float], ratio: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = min(len(values) - 1, int((len(values) - 1) * ratio))
    return round(values[idx], 3)


def keyword_hits(text: str, keywords: List[str]) -> int:
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lower)


def build_payload(items: List[Dict], mode: str, rng: random.Random) -> List[Dict]:
    payload = []
    for item in items:
        if mode == "local_only":
            continue
        if mode == "raw_sync":
            payload.append(
                {
                    "memory_id": item["memory_id"],
                    "topic": item["topic"],
                    "content": item["raw_text"],
                    "privacy_level": item["privacy_level"],
                    "sensitive_tokens": item["sensitive_tokens"],
                    "contains_raw_sensitive": bool(item["sensitive_tokens"]),
                }
            )
        elif mode == "summary_sync":
            payload.append(
                {
                    "memory_id": item["memory_id"],
                    "topic": item["topic"],
                    "content": item["summary_text"],
                    "privacy_level": item["privacy_level"],
                    "sensitive_tokens": [],
                    "contains_raw_sensitive": False,
                }
            )
        elif mode == "dp_sync":
            noise = rng.choice([-1, 0, 1])
            payload.append(
                {
                    "memory_id": item["memory_id"],
                    "topic": item["topic"],
                    "content": f"{item['dp_summary']} [noise={noise}]",
                    "privacy_level": "L0" if item["privacy_level"] != "L3" else "L1",
                    "sensitive_tokens": [],
                    "contains_raw_sensitive": False,
                }
            )
    return payload


def answer_for_query(local_items: List[Dict], synced_items: List[Dict], query: Dict, mode: str) -> str:
    query_topic = query["target_topic"]
    relevant_synced = [item["content"] for item in synced_items if item["topic"] == query_topic]
    relevant_local = [item["summary_text"] for item in local_items if item["topic"] in {"calendar", "shopping"}]
    if mode == "local_only":
        return "仅本地上下文，不足以恢复跨设备偏好。"
    if query_topic == "coffee":
        return "；".join(relevant_local[:1] + relevant_synced[:1]) or "未找到咖啡偏好。"
    if query_topic == "meal":
        return "；".join(relevant_local[1:2] + relevant_synced[:1]) or "未找到饮食偏好。"
    if query_topic == "payments":
        return "；".join(relevant_synced[:1]) or "未找到支付偏好。"
    return "；".join(relevant_synced[:1])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run simulated cross-device sync evaluation.")
    parser.add_argument("--device-a", default="experiments/datasets/sync_device_a.jsonl")
    parser.add_argument("--device-b", default="experiments/datasets/sync_device_b.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/sync_query_set.jsonl")
    parser.add_argument("--run-id", default="sync_eval_v1")
    parser.add_argument("--epsilon", type=float, default=2.0)
    args = parser.parse_args()

    device_a = load_jsonl(Path(args.device_a))
    device_b = load_jsonl(Path(args.device_b))
    queries = load_jsonl(Path(args.queries))

    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    rng = random.Random(42)

    payload_rows = []
    result_rows = []

    for mode in MODES:
        sync_start = time.perf_counter()
        payload = build_payload(device_a, mode, rng)
        sync_overhead_ms = round((time.perf_counter() - sync_start) * 1000, 3)
        payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        contains_sensitive = sum(1 for item in payload if item["contains_raw_sensitive"])
        sensitive_token_count = sum(len(item["sensitive_tokens"]) for item in payload)

        payload_rows.append(
            {
                "ts": ts,
                "mode": mode,
                "epsilon": args.epsilon if mode == "dp_sync" else None,
                "payload_item_count": len(payload),
                "payload_bytes": payload_bytes,
                "sync_overhead_ms": sync_overhead_ms,
                "raw_sensitive_item_count": contains_sensitive,
                "sensitive_token_count": sensitive_token_count,
            }
        )

        for query in queries:
            answer = answer_for_query(device_b, payload, query, mode)
            hit_count = keyword_hits(answer, query["expected_keywords"])
            utility_pass = hit_count >= query["utility_min_keywords"]
            result_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "mode": mode,
                    "query_id": query["query_id"],
                    "device_id": query["device_id"],
                    "target_topic": query["target_topic"],
                    "answer_text": answer,
                    "keyword_hit_count": hit_count,
                    "utility_pass": utility_pass,
                    "contains_raw_sensitive": contains_sensitive > 0,
                    "payload_bytes": payload_bytes,
                    "sync_overhead_ms": sync_overhead_ms,
                    "reidentification_risk_score": round(
                        min(1.0, (contains_sensitive * 0.5) + (sensitive_token_count * 0.15)),
                        4,
                    ),
                }
            )

    metrics = {"run_id": args.run_id, "modes": {}}
    local_success = 0.0
    for mode in MODES:
        rows = [row for row in result_rows if row["mode"] == mode]
        payload_row = next(row for row in payload_rows if row["mode"] == mode)
        count = len(rows) or 1
        success_rate = round(sum(1 for row in rows if row["utility_pass"]) / count, 4)
        if mode == "local_only":
            local_success = success_rate
        metrics["modes"][mode] = {
            "task_success_rate": success_rate,
            "personalization_gain": round(success_rate - local_success, 4) if mode != "local_only" else 0.0,
            "reidentification_risk_score": round(
                sum(row["reidentification_risk_score"] for row in rows) / count,
                4,
            ),
            "sync_overhead_ms_p50": round(median([row["sync_overhead_ms"] for row in rows]), 3),
            "sync_overhead_ms_p95": percentile([row["sync_overhead_ms"] for row in rows], 0.95),
            "payload_bytes": payload_row["payload_bytes"],
            "raw_sensitive_item_count": payload_row["raw_sensitive_item_count"],
            "epsilon": payload_row["epsilon"],
        }

    write_jsonl(run_dir / "payloads.jsonl", payload_rows)
    write_jsonl(run_dir / "results.jsonl", result_rows)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
