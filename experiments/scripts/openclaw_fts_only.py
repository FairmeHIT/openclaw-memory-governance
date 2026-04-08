#!/usr/bin/env python3

import argparse
import json
import os
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


def scrubbed_env() -> Dict[str, str]:
    env = dict(os.environ)
    for key in ENV_UNSET_KEYS:
        env.pop(key, None)
    return env


def run_openclaw(args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["openclaw", *args],
        capture_output=True,
        text=True,
        env=scrubbed_env(),
    )


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


def print_proc(proc: subprocess.CompletedProcess) -> int:
    if proc.stdout:
        sys.stdout.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        if not proc.stderr.endswith("\n"):
            sys.stderr.write("\n")
    return proc.returncode


def cmd_status(args: argparse.Namespace) -> int:
    proc = run_openclaw(["memory", "status", "--agent", args.agent, *([] if not args.deep else ["--deep"]), *([] if not args.json else ["--json"])])
    return print_proc(proc)


def cmd_index(args: argparse.Namespace) -> int:
    proc = run_openclaw(["memory", "index", "--agent", args.agent, *([] if not args.force else ["--force"])])
    return print_proc(proc)


def cmd_search(args: argparse.Namespace) -> int:
    cli_args = [
        "memory",
        "search",
        "--agent",
        args.agent,
        "--query",
        args.query,
        "--max-results",
        str(args.max_results),
    ]
    if args.json:
        cli_args.append("--json")
    proc = run_openclaw(cli_args)
    return print_proc(proc)


def cmd_ensure(args: argparse.Namespace) -> int:
    rows = []
    exit_code = 0
    for agent in args.agents:
        status_proc = run_openclaw(["memory", "status", "--agent", agent, "--deep", "--json"])
        status_payload = parse_json_from_stdout(status_proc.stdout)
        status_row = status_payload[0] if isinstance(status_payload, list) and status_payload else status_payload
        status_section = status_row.get("status", {}) if isinstance(status_row, dict) else {}
        custom_section = status_section.get("custom", {})
        index_proc = run_openclaw(["memory", "index", "--agent", agent, "--force"])
        rows.append(
            {
                "agent_id": agent,
                "status_exit_code": status_proc.returncode,
                "provider": status_section.get("provider"),
                "search_mode": custom_section.get("searchMode"),
                "index_exit_code": index_proc.returncode,
            }
        )
        if status_proc.returncode != 0 or index_proc.returncode != 0:
            exit_code = 1

    payload = {"agents": rows}
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run OpenClaw memory commands in env-scrubbed fts-only mode.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Run openclaw memory status with embedding env removed.")
    status_parser.add_argument("--agent", default="assistant")
    status_parser.add_argument("--deep", action="store_true")
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(func=cmd_status)

    index_parser = subparsers.add_parser("index", help="Run openclaw memory index with embedding env removed.")
    index_parser.add_argument("--agent", default="assistant")
    index_parser.add_argument("--force", action="store_true")
    index_parser.set_defaults(func=cmd_index)

    search_parser = subparsers.add_parser("search", help="Run openclaw memory search with embedding env removed.")
    search_parser.add_argument("--agent", default="assistant")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--max-results", type=int, default=5)
    search_parser.add_argument("--json", action="store_true")
    search_parser.set_defaults(func=cmd_search)

    ensure_parser = subparsers.add_parser("ensure", help="Check status and rebuild native FTS indexes for a list of agents.")
    ensure_parser.add_argument("--agents", nargs="*", default=DEFAULT_AGENTS)
    ensure_parser.add_argument("--output")
    ensure_parser.set_defaults(func=cmd_ensure)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
