#!/usr/bin/env python3

import argparse
import json
import random
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Dict, List


MODES = ["local_only", "raw_sync", "summary_sync", "policy_sync", "dp_sync"]


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


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def keyword_hits(text: str, keywords: List[str]) -> int:
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lower)


def mode_content(item: Dict, mode: str, rng: random.Random) -> str:
    if mode == "raw_sync":
        return item["raw_text"]
    if mode == "summary_sync":
        return item["summary_text"]
    if mode == "policy_sync":
        return item["summary_text"]
    if mode == "dp_sync":
        noise = rng.choice([-1, 0, 1])
        return f"{item['dp_summary']} [noise={noise}]"
    return ""


def build_payload(items: List[Dict], mode: str, rng: random.Random) -> List[Dict]:
    payload = []
    for item in items:
        if mode == "local_only":
            continue

        if mode in {"policy_sync", "dp_sync"} and item["privacy_level"] == "L3":
            continue

        contains_raw_sensitive = mode == "raw_sync" and bool(item.get("sensitive_tokens"))
        payload.append(
            {
                "origin_memory_id": item["memory_id"],
                "device_id": "device_a",
                "topic": item["topic"],
                "domain": item["domain"],
                "privacy_level": item["privacy_level"] if mode != "dp_sync" else "L0",
                "content": mode_content(item, mode, rng),
                "sync_mode": mode,
                "lifecycle": "active",
                "contains_raw_sensitive": contains_raw_sensitive,
                "sensitive_tokens": item.get("sensitive_tokens", []) if contains_raw_sensitive else [],
                "policy_metadata": mode in {"policy_sync", "dp_sync"},
            }
        )
    return payload


def build_tombstones(items: List[Dict], mode: str, revoked_topics: set[str]) -> List[Dict]:
    if mode not in {"policy_sync", "dp_sync"}:
        return []
    return [
        {
            "origin_memory_id": item["memory_id"],
            "topic": item["topic"],
            "lifecycle": "revoked",
            "reason": "user_revoked",
            "policy_metadata": True,
        }
        for item in items
        if item["topic"] in revoked_topics
    ]


def apply_payload(device_b_items: List[Dict], payload: List[Dict]) -> List[Dict]:
    state = [
        {
            "origin_memory_id": item["memory_id"],
            "device_id": item["device_id"],
            "topic": item["topic"],
            "domain": item["domain"],
            "privacy_level": item["privacy_level"],
            "content": item["summary_text"],
            "sync_mode": "local",
            "lifecycle": "active",
            "contains_raw_sensitive": False,
            "sensitive_tokens": [],
            "policy_metadata": True,
        }
        for item in device_b_items
    ]
    state.extend(payload)
    return state


def apply_tombstones(state: List[Dict], tombstones: List[Dict]) -> List[Dict]:
    revoked_ids = {item["origin_memory_id"] for item in tombstones}
    if not revoked_ids:
        return state
    next_state = []
    for item in state:
        if item["origin_memory_id"] in revoked_ids:
            next_state.append({**item, "lifecycle": "revoked"})
        else:
            next_state.append(item)
    return next_state


def answer_query(state: List[Dict], query: Dict) -> str:
    matches = [
        item["content"]
        for item in state
        if item["lifecycle"] == "active" and item["topic"] == query["target_topic"]
    ]
    return "；".join(matches[:2])


def reidentification_risk(payload: List[Dict]) -> float:
    sensitive_items = sum(1 for item in payload if item["contains_raw_sensitive"])
    sensitive_tokens = sum(len(item.get("sensitive_tokens", [])) for item in payload)
    return round(min(1.0, sensitive_items * 0.5 + sensitive_tokens * 0.15), 4)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a single-host dual-device sync evaluation with local device state directories."
    )
    parser.add_argument("--device-a", default="experiments/datasets/sync_device_a.jsonl")
    parser.add_argument("--device-b", default="experiments/datasets/sync_device_b.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/sync_query_set.jsonl")
    parser.add_argument("--run-id", default="local_dual_device_sync_v1")
    parser.add_argument("--revoked-topic", default="payments")
    parser.add_argument("--epsilon", type=float, default=2.0)
    args = parser.parse_args()

    run_dir = Path("experiments/runs") / args.run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    device_a_items = load_jsonl(Path(args.device_a))
    device_b_items = load_jsonl(Path(args.device_b))
    queries = load_jsonl(Path(args.queries))
    revoked_topics = {args.revoked_topic}
    ts = datetime.now(timezone.utc).isoformat()
    rng = random.Random(42)

    payload_rows = []
    query_rows = []
    revoke_rows = []
    metrics = {"run_id": args.run_id, "modes": {}}

    for mode in MODES:
        mode_dir = run_dir / mode
        write_jsonl(mode_dir / "device_a" / "memory_state_initial.jsonl", device_a_items)
        write_jsonl(mode_dir / "device_b" / "memory_state_initial.jsonl", device_b_items)

        start = time.perf_counter()
        payload = build_payload(device_a_items, mode, rng)
        sync_overhead_ms = round((time.perf_counter() - start) * 1000, 3)
        state_after_sync = apply_payload(device_b_items, payload)
        payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

        write_jsonl(mode_dir / "payload_initial.jsonl", payload)
        write_jsonl(mode_dir / "device_b" / "memory_state_after_sync.jsonl", state_after_sync)

        initial_results = []
        for query in queries:
            answer = answer_query(state_after_sync, query)
            hits = keyword_hits(answer, query["expected_keywords"])
            utility_pass = hits >= query["utility_min_keywords"]
            row = {
                "ts": ts,
                "run_id": args.run_id,
                "mode": mode,
                "phase": "after_initial_sync",
                "query_id": query["query_id"],
                "target_topic": query["target_topic"],
                "answer_text": answer or None,
                "keyword_hit_count": hits,
                "utility_pass": utility_pass,
            }
            initial_results.append(row)
            query_rows.append(row)

        tombstones = build_tombstones(device_a_items, mode, revoked_topics)
        state_after_revoke = apply_tombstones(state_after_sync, tombstones)
        write_jsonl(mode_dir / "payload_revoke.jsonl", tombstones)
        write_jsonl(mode_dir / "device_b" / "memory_state_after_revoke.jsonl", state_after_revoke)
        revoke_rows.append(
            {
                "ts": ts,
                "run_id": args.run_id,
                "mode": mode,
                "revoked_topics": sorted(revoked_topics),
                "tombstone_count": len(tombstones),
                "revocation_payload_bytes": len(json.dumps(tombstones, ensure_ascii=False).encode("utf-8")),
            }
        )

        stale_results = []
        for query in queries:
            if query["target_topic"] not in revoked_topics:
                continue
            answer = answer_query(state_after_revoke, query)
            hits = keyword_hits(answer, query["expected_keywords"])
            stale_recall = hits >= query["utility_min_keywords"]
            row = {
                "ts": ts,
                "run_id": args.run_id,
                "mode": mode,
                "phase": "after_revoke",
                "query_id": query["query_id"],
                "target_topic": query["target_topic"],
                "answer_text": answer or None,
                "keyword_hit_count": hits,
                "stale_recall": stale_recall,
            }
            stale_results.append(row)
            query_rows.append(row)

        count = len(initial_results) or 1
        success_rate = sum(1 for row in initial_results if row["utility_pass"]) / count
        stale_recall_count = sum(1 for row in stale_results if row["stale_recall"])
        sensitive_items = sum(1 for item in payload if item["contains_raw_sensitive"])
        payload_rows.append(
            {
                "ts": ts,
                "run_id": args.run_id,
                "mode": mode,
                "payload_item_count": len(payload),
                "payload_bytes": payload_bytes,
                "raw_sensitive_item_count": sensitive_items,
                "reidentification_risk_score": reidentification_risk(payload),
                "sync_overhead_ms": sync_overhead_ms,
                "epsilon": args.epsilon if mode == "dp_sync" else None,
            }
        )
        metrics["modes"][mode] = {
            "task_success_rate_after_initial_sync": round(success_rate, 4),
            "personalization_gain": round(success_rate, 4),
            "reidentification_risk_score": reidentification_risk(payload),
            "raw_sensitive_item_count": sensitive_items,
            "payload_bytes": payload_bytes,
            "tombstone_count": len(tombstones),
            "revocation_enforced": stale_recall_count == 0,
            "stale_recall_count_after_revoke": stale_recall_count,
            "sync_overhead_ms_p50": round(median([sync_overhead_ms]), 3),
            "epsilon": args.epsilon if mode == "dp_sync" else None,
        }

    write_jsonl(run_dir / "payloads.jsonl", payload_rows)
    write_jsonl(run_dir / "query_results.jsonl", query_rows)
    write_jsonl(run_dir / "revocations.jsonl", revoke_rows)
    write_json(run_dir / "metrics.json", metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
