#!/usr/bin/env python3

import argparse
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, List


def load_jsonl(path: Path) -> List[Dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def initialize_store(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_records (
                origin_memory_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                domain TEXT NOT NULL,
                privacy_level TEXT NOT NULL,
                content TEXT NOT NULL,
                lifecycle TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS applied_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outbox_events (
                event_id TEXT PRIMARY KEY,
                event_json TEXT NOT NULL
            );
            """
        )


def append_outbox_event(store: Path, event: Dict) -> None:
    with sqlite3.connect(store) as conn:
        conn.execute(
            "INSERT INTO outbox_events(event_id, event_json) VALUES (?, ?)",
            (event["event_id"], json.dumps(event, ensure_ascii=False, sort_keys=True)),
        )


def apply_event(store: Path, event: Dict) -> bool:
    event_type = event.get("event_type")
    if event_type not in {"upsert", "tombstone"}:
        raise ValueError("event_type must be upsert or tombstone")
    with sqlite3.connect(store) as conn:
        existing = conn.execute(
            "SELECT 1 FROM applied_events WHERE event_id = ?", (event["event_id"],)
        ).fetchone()
        if existing:
            return False
        if event_type == "upsert":
            current = conn.execute(
                "SELECT lifecycle FROM memory_records WHERE origin_memory_id = ?",
                (event["origin_memory_id"],),
            ).fetchone()
            if current is None:
                conn.execute(
                    """
                    INSERT INTO memory_records(
                        origin_memory_id, topic, domain, privacy_level, content, lifecycle
                    ) VALUES (?, ?, ?, ?, ?, 'active')
                    """,
                    (
                        event["origin_memory_id"],
                        event["topic"],
                        event["domain"],
                        event["privacy_level"],
                        event["content"],
                    ),
                )
            elif current[0] != "revoked":
                conn.execute(
                    """
                    UPDATE memory_records
                    SET topic = ?, domain = ?, privacy_level = ?, content = ?
                    WHERE origin_memory_id = ?
                    """,
                    (
                        event["topic"],
                        event["domain"],
                        event["privacy_level"],
                        event["content"],
                        event["origin_memory_id"],
                    ),
                )
        else:
            conn.execute(
                """
                INSERT INTO memory_records(
                    origin_memory_id, topic, domain, privacy_level, content, lifecycle
                ) VALUES (?, ?, 'unknown', 'unknown', '', 'revoked')
                ON CONFLICT(origin_memory_id) DO UPDATE SET lifecycle = 'revoked'
                """,
                (event["origin_memory_id"], event["topic"]),
            )
        conn.execute(
            "INSERT INTO applied_events(event_id, event_type) VALUES (?, ?)",
            (event["event_id"], event_type),
        )
    return True


def active_records(store: Path, topic: str) -> List[Dict]:
    with sqlite3.connect(store) as conn:
        rows = conn.execute(
            """
            SELECT origin_memory_id, topic, domain, privacy_level, content
            FROM memory_records
            WHERE topic = ? AND lifecycle = 'active'
            ORDER BY origin_memory_id
            """,
            (topic,),
        ).fetchall()
    fields = ["origin_memory_id", "topic", "domain", "privacy_level", "content"]
    return [dict(zip(fields, row)) for row in rows]


def policy_sync_events(items: List[Dict]) -> List[Dict]:
    return [
        {
            "event_id": f"upsert:{item['memory_id']}",
            "event_type": "upsert",
            "origin_memory_id": item["memory_id"],
            "topic": item["topic"],
            "domain": item["domain"],
            "privacy_level": item["privacy_level"],
            "content": item["summary_text"],
        }
        for item in items
        if item["privacy_level"] != "L3"
    ]


def matches_query(records: List[Dict], query: Dict) -> bool:
    text = "；".join(record["content"] for record in records).lower()
    return sum(keyword.lower() in text for keyword in query["expected_keywords"]) >= query["utility_min_keywords"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate persistent two-store policy sync, tombstone delivery, and late-event safety."
    )
    parser.add_argument("--device-a", default="experiments/datasets/sync_device_a.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/sync_query_set.jsonl")
    parser.add_argument("--run-id", default="dual_store_sync_v1")
    parser.add_argument("--revoked-topic", default="payments")
    args = parser.parse_args()

    run_dir = Path("experiments/runs") / args.run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    device_a = run_dir / "device_a.sqlite"
    device_b = run_dir / "device_b.sqlite"
    initialize_store(device_a)
    initialize_store(device_b)

    source_items = load_jsonl(Path(args.device_a))
    queries = load_jsonl(Path(args.queries))
    events = policy_sync_events(source_items)
    trace_rows = []
    for event in events:
        append_outbox_event(device_a, event)
        applied = apply_event(device_b, event)
        trace_rows.append({"phase": "initial_delivery", "event_id": event["event_id"], "applied": applied})

    initial_successes = sum(
        matches_query(active_records(device_b, query["target_topic"]), query) for query in queries
    )
    revoked_item = next(item for item in source_items if item["topic"] == args.revoked_topic)
    revoke_event = {
        "event_id": f"tombstone:{revoked_item['memory_id']}",
        "event_type": "tombstone",
        "origin_memory_id": revoked_item["memory_id"],
        "topic": revoked_item["topic"],
    }
    append_outbox_event(device_a, revoke_event)
    revoked_queries = [query for query in queries if query["target_topic"] == args.revoked_topic]
    stale_before_delivery = sum(
        matches_query(active_records(device_b, query["target_topic"]), query) for query in revoked_queries
    )
    tombstone_applied = apply_event(device_b, revoke_event)
    duplicate_rejected = not apply_event(device_b, revoke_event)
    stale_after_delivery = sum(
        matches_query(active_records(device_b, query["target_topic"]), query) for query in revoked_queries
    )

    late_upsert = {
        **next(event for event in events if event["origin_memory_id"] == revoked_item["memory_id"]),
        "event_id": f"late:{revoked_item['memory_id']}",
    }
    append_outbox_event(device_a, late_upsert)
    late_event_applied = apply_event(device_b, late_upsert)
    late_upsert_blocked = not active_records(device_b, args.revoked_topic)
    trace_rows.extend(
        [
            {"phase": "tombstone_delivery", "event_id": revoke_event["event_id"], "applied": tombstone_applied},
            {"phase": "tombstone_replay", "event_id": revoke_event["event_id"], "applied": not duplicate_rejected},
            {"phase": "late_upsert", "event_id": late_upsert["event_id"], "applied": late_event_applied},
        ]
    )

    metrics = {
        "run_id": args.run_id,
        "persistent_store_count": 2,
        "initial_upsert_event_count": len(events),
        "initial_task_success_rate": round(initial_successes / (len(queries) or 1), 4),
        "stale_recall_before_tombstone_delivery": stale_before_delivery,
        "stale_recall_after_tombstone_delivery": stale_after_delivery,
        "tombstone_persisted": tombstone_applied,
        "tombstone_idempotent": duplicate_rejected,
        "late_upsert_event_applied": late_event_applied,
        "late_upsert_blocked": late_upsert_blocked,
        "l3_source_count": sum(item["privacy_level"] == "L3" for item in source_items),
        "l3_excluded_from_sync": all(event["privacy_level"] != "L3" for event in events),
    }
    write_jsonl(run_dir / "sync_trace.jsonl", trace_rows)
    write_json(run_dir / "metrics.json", metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
