#!/usr/bin/env python3

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


ENV_UNSET_KEYS = [
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "VOYAGE_API_KEY",
    "MISTRAL_API_KEY",
]
DEFAULT_AGENTS = ["assistant", "main", "code", "content", "zhixi"]


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


def scrubbed_env() -> Dict[str, str]:
    env = dict(os.environ)
    for key in ENV_UNSET_KEYS:
        env.pop(key, None)
    return env


def run_command(args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, env=scrubbed_env())


def parse_json_from_stdout(stdout: str) -> Dict:
    for idx, char in enumerate(stdout):
        if char == "{":
            try:
                return json.loads(stdout[idx:])
            except json.JSONDecodeError:
                continue
    return {}


def db_path(openclaw_home: Path, agent_id: str) -> Path:
    suffix = "main" if agent_id == "main" else agent_id
    return openclaw_home / "memory" / f"{suffix}.sqlite"


def query_for_agent(queries: List[Dict], agent_id: str) -> Dict:
    for row in queries:
        if row["agent_id"] == agent_id and row["purpose"] == "task_continuity":
            return row
    raise ValueError(f"No validation query found for agent {agent_id}")


def sqlite_counts(path: Path) -> Dict[str, int]:
    conn = sqlite3.connect(path)
    try:
        chunks = conn.execute("select count(*) from chunks").fetchone()[0]
        files = conn.execute("select count(*) from files").fetchone()[0]
        fts_rows = conn.execute("select count(*) from chunks_fts").fetchone()[0]
    finally:
        conn.close()
    return {"files": files, "chunks": chunks, "fts_rows": fts_rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore and validate OpenClaw native FTS indexes across agents.")
    parser.add_argument("--openclaw-home", default=str(Path.home() / ".openclaw"))
    parser.add_argument("--queries", default="experiments/datasets/native_fts_query_set.jsonl")
    parser.add_argument("--run-id", default="native_fts_validation_v1")
    parser.add_argument("--agents", nargs="*", default=DEFAULT_AGENTS)
    args = parser.parse_args()

    openclaw_home = Path(args.openclaw_home)
    queries = load_jsonl(Path(args.queries))
    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    details = []

    adapter_script = Path(__file__).resolve().parent / "openclaw_guard_adapter.py"

    for agent_id in args.agents:
        selected_query = query_for_agent(queries, agent_id)

        index_proc = run_command([
            "openclaw",
            "memory",
            "index",
            "--agent",
            agent_id,
            "--force",
        ])

        database_path = db_path(openclaw_home, agent_id)
        counts = sqlite_counts(database_path)

        search_proc = run_command([
            "openclaw",
            "memory",
            "search",
            "--agent",
            agent_id,
            "--json",
            "--query",
            selected_query["query"],
            "--max-results",
            "5",
        ])
        search_payload = parse_json_from_stdout(search_proc.stdout)
        search_results = search_payload.get("results") or []

        adapter_run_id = f"{args.run_id}_{agent_id}"
        adapter_proc = subprocess.run(
            [
                sys.executable,
                str(adapter_script),
                "--agent",
                agent_id,
                "--purpose",
                selected_query["purpose"],
                "--query",
                selected_query["query"],
                "--run-id",
                adapter_run_id,
            ],
            capture_output=True,
            text=True,
            env=scrubbed_env(),
        )
        adapter_payload = parse_json_from_stdout(adapter_proc.stdout)

        details.append(
            {
                "agent_id": agent_id,
                "query_id": selected_query["query_id"],
                "query": selected_query["query"],
                "index_exit_code": index_proc.returncode,
                "db_path": str(database_path),
                "db_files": counts["files"],
                "db_chunks": counts["chunks"],
                "db_fts_rows": counts["fts_rows"],
                "native_search_exit_code": search_proc.returncode,
                "native_result_count": len(search_results),
                "native_top_path": search_results[0]["path"] if search_results else None,
                "native_top_score": search_results[0]["score"] if search_results else None,
                "adapter_exit_code": adapter_proc.returncode,
                "adapter_candidate_source": adapter_payload.get("candidate_source"),
                "adapter_allowed_count": len(adapter_payload.get("allowed") or []),
                "adapter_downgraded_count": len(adapter_payload.get("downgraded") or []),
                "adapter_sandboxed_count": len(adapter_payload.get("sandboxed") or []),
                "adapter_denied_count": len(adapter_payload.get("denied") or []),
            }
        )

    metrics = {
        "run_id": args.run_id,
        "agents_checked": len(details),
        "agents_with_index_rows": sum(1 for row in details if row["db_chunks"] > 0 and row["db_fts_rows"] > 0),
        "native_search_success_rate": round(
            sum(1 for row in details if row["native_result_count"] > 0) / len(details),
            4,
        ) if details else 0.0,
        "guard_native_cli_rate": round(
            sum(1 for row in details if row["adapter_candidate_source"] == "native_cli") / len(details),
            4,
        ) if details else 0.0,
    }

    write_jsonl(run_dir / "details.jsonl", details)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"metrics": metrics, "details": details}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
