#!/usr/bin/env python3

import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize governance SQLite database.")
    parser.add_argument(
        "--db",
        default="experiments/governance.sqlite",
        help="Path to the governance SQLite database.",
    )
    parser.add_argument(
        "--schema",
        default="experiments/schemas/memory_governance.sql",
        help="Path to the governance schema file.",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = Path(args.schema).read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"Initialized governance database at {db_path}")


if __name__ == "__main__":
    main()
