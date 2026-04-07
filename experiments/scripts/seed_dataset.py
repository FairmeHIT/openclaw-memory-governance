#!/usr/bin/env python3

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed governance database from memory_samples.jsonl.")
    parser.add_argument(
        "--db",
        default="experiments/governance.sqlite",
        help="Path to the governance SQLite database.",
    )
    parser.add_argument(
        "--dataset",
        default="experiments/datasets/memory_samples.jsonl",
        help="Path to the labeled memory dataset.",
    )
    parser.add_argument(
        "--table",
        default="memory_governance",
        help="Target governance table name.",
    )
    args = parser.parse_args()

    rows = []
    timestamp = datetime.now(timezone.utc).isoformat()
    dataset_path = Path(args.dataset)
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        chunk_id = item.get("chunk_id", item["memory_id"])
        file_path = item.get("file_path", f"dataset://{item['workspace']}/{item['memory_id']}")
        rows.append(
            (
                chunk_id,
                item["memory_id"],
                file_path,
                item["agent_id"],
                item["workspace"],
                item["domain"],
                item["privacy_level"],
                item["source_trust"],
                json.dumps(item["purpose_allow"], ensure_ascii=True),
                item["lifecycle"],
                item["sync_policy"],
                item["index_policy"],
                item.get("notes", ""),
                timestamp,
                timestamp,
            )
        )

    conn = sqlite3.connect(args.db)
    try:
        conn.execute(f"DELETE FROM {args.table}")
        conn.executemany(
            f"""
            INSERT INTO {args.table} (
              chunk_id, memory_id, file_path, agent_id, workspace, domain,
              privacy_level, source_trust, purpose_allow, lifecycle,
              sync_policy, index_policy, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()

    print(f"Seeded {len(rows)} governance rows into {args.db}")


if __name__ == "__main__":
    main()
