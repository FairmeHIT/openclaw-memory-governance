#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def parse_json_from_stdout(stdout: str):
    for idx, char in enumerate(stdout):
        if char == "{":
            try:
                return json.loads(stdout[idx:])
            except json.JSONDecodeError:
                continue
        if char == "[":
            try:
                return json.loads(stdout[idx:])
            except json.JSONDecodeError:
                continue
    return {}


def load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def workspace_relative_path(file_path: str, workspace_name: str, openclaw_home: Path) -> str:
    workspace_root = openclaw_home / workspace_name
    try:
        return str(Path(file_path).resolve().relative_to(workspace_root.resolve()))
    except ValueError:
        return Path(file_path).name


def render_result(row: Dict, workspace_name: str, openclaw_home: Path, decision: str) -> Dict:
    if decision == "allow":
        snippet = row["text"]
    elif decision == "downgrade":
        snippet = row["summary"]
    else:
        snippet = row.get("status", decision)
    return {
        "id": row["chunk_id"],
        "path": workspace_relative_path(row["file_path"], workspace_name, openclaw_home),
        "startLine": None,
        "endLine": None,
        "score": None,
        "textScore": None,
        "snippet": snippet,
        "source": "memory",
        "governance": {
            "decision": decision,
            "privacyLevel": row["privacy_level"],
        },
    }


def print_human(payload: Dict) -> None:
    results = payload.get("results") or []
    if not results:
        print("No governed memory results.")
        return
    for idx, item in enumerate(results, start=1):
        decision = item.get("governance", {}).get("decision", "allow")
        privacy = item.get("governance", {}).get("privacyLevel", "L0")
        print(f"{idx}. [{decision}/{privacy}] {item['path']}")
        print(item["snippet"])
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Guarded replacement for `openclaw memory search`.")
    parser.add_argument("query", nargs="?", help="Search query.")
    parser.add_argument("--query", dest="query_flag", help="Search query.")
    parser.add_argument("--agent", default="assistant")
    parser.add_argument("--purpose", default="task_continuity")
    parser.add_argument("--workspace")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--openclaw-home", default=str(Path.home() / ".openclaw"))
    parser.add_argument("--run-id", default="openclaw_guarded_search")
    args = parser.parse_args()

    query = args.query_flag or args.query
    if not query:
        raise SystemExit("Query is required. Use positional query or --query.")

    openclaw_home = Path(args.openclaw_home)
    adapter_script = Path(__file__).resolve().parent / "openclaw_guard_adapter.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(adapter_script),
            "--agent",
            args.agent,
            "--purpose",
            args.purpose,
            "--query",
            query,
            "--top-k",
            str(args.max_results),
            "--run-id",
            args.run_id,
            *(["--workspace", args.workspace] if args.workspace else []),
            "--openclaw-home",
            str(openclaw_home),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout)
        raise SystemExit(proc.returncode)

    adapter_payload = parse_json_from_stdout(proc.stdout)
    if not isinstance(adapter_payload, dict):
        raise SystemExit("Guard adapter returned invalid payload.")

    run_dir = Path("experiments/runs") / args.run_id
    governed_rows = {
        row["chunk_id"]: row
        for row in load_jsonl(run_dir / "governed_chunks.jsonl")
    }

    workspace_name = adapter_payload.get("workspace") or args.workspace or f"workspace-{args.agent}"
    results = []
    for row in adapter_payload.get("allowed") or []:
        enriched = dict(row)
        enriched["file_path"] = governed_rows.get(row["chunk_id"], {}).get("file_path", "")
        results.append(render_result(enriched, workspace_name, openclaw_home, "allow"))
    for row in adapter_payload.get("downgraded") or []:
        enriched = dict(row)
        enriched["file_path"] = governed_rows.get(row["chunk_id"], {}).get("file_path", "")
        results.append(render_result(enriched, workspace_name, openclaw_home, "downgrade"))

    payload = {
        "results": results,
        "governance": {
            "candidateSource": adapter_payload.get("candidate_source"),
            "allowedCount": len(adapter_payload.get("allowed") or []),
            "downgradedCount": len(adapter_payload.get("downgraded") or []),
            "sandboxedCount": len(adapter_payload.get("sandboxed") or []),
            "deniedCount": len(adapter_payload.get("denied") or []),
            "purpose": adapter_payload.get("purpose"),
            "agentId": adapter_payload.get("agent_id"),
        },
        "sandboxed": adapter_payload.get("sandboxed") or [],
        "denied": adapter_payload.get("denied") or [],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human(payload)


if __name__ == "__main__":
    main()
