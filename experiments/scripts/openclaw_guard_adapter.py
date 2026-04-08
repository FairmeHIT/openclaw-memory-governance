#!/usr/bin/env python3

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")
WORKSPACE_FOR_AGENT = {
    "main": "workspace-main",
    "code": "workspace-code",
    "content": "workspace-content",
    "assistant": "workspace-assistant",
    "zhixi": "workspace-zhixi",
}
WORKSPACE_DOMAIN = {
    "workspace-assistant": "personal",
    "workspace-main": "work",
    "workspace-code": "work",
    "workspace-content": "third_party",
    "workspace-zhixi": "personal",
}


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def score(query: str, text: str) -> int:
    query_terms = Counter(tokenize(query))
    text_terms = Counter(tokenize(text))
    return sum(min(query_terms[token], text_terms[token]) for token in query_terms)


def summarize_text(text: str, max_len: int = 96) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


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


def ensure_governed_dataset(output_path: Path, openclaw_home: Path) -> None:
    script_path = Path(__file__).resolve().parents[2] / "skills" / "memory-classify" / "scripts" / "classify_openclaw_memory.py"
    subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--openclaw-home",
            str(openclaw_home),
            "--output",
            str(output_path),
            "--mode",
            "chunk",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def db_path_for_agent(openclaw_home: Path, agent_id: str) -> Path:
    suffix = "main" if agent_id == "main" else agent_id
    return openclaw_home / "memory" / f"{suffix}.sqlite"


def parse_json_from_cli(stdout: str) -> Dict:
    for idx, char in enumerate(stdout):
        if char == "{":
            try:
                return json.loads(stdout[idx:])
            except json.JSONDecodeError:
                continue
    return {}


def fetch_native_candidates_via_cli(agent_id: str, query: str, top_k: int) -> Tuple[str, List[Dict]]:
    proc = subprocess.run(
        [
            "env",
            "-u",
            "OPENAI_API_KEY",
            "-u",
            "GEMINI_API_KEY",
            "-u",
            "VOYAGE_API_KEY",
            "-u",
            "MISTRAL_API_KEY",
            "openclaw",
            "memory",
            "search",
            "--agent",
            agent_id,
            "--json",
            "--query",
            query,
            "--max-results",
            str(top_k),
        ],
        capture_output=True,
        text=True,
    )
    payload = parse_json_from_cli(proc.stdout)
    results = payload.get("results") or []
    if results:
        return "native_cli", results
    return "native_cli_empty", []


def fetch_native_candidates_sqlite(db_path: Path, query: str, top_k: int) -> Tuple[str, List[Dict]]:
    if not db_path.exists():
        return "missing_db", []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        chunk_count = conn.execute("select count(*) from chunks").fetchone()[0]
        if chunk_count == 0:
            return "empty_index", []

        fts_query = " ".join(tokenize(query)).strip()
        if not fts_query:
            return "empty_query", []

        rows = conn.execute(
            """
            select c.id as native_chunk_id, c.path, c.start_line, c.end_line, c.text,
                   bm25(chunks_fts) as rank
            from chunks_fts
            join chunks c on c.id = chunks_fts.id
            where chunks_fts match ?
            order by rank
            limit ?
            """,
            (fts_query, top_k),
        ).fetchall()
        return "native_fts", [dict(row) for row in rows]
    except sqlite3.OperationalError as exc:
        return f"native_error:{exc}", []
    finally:
        conn.close()


def map_native_to_governed(native_rows: List[Dict], governed_rows: List[Dict], workspace_root: Path) -> List[Dict]:
    by_path: Dict[str, List[Dict]] = {}
    for row in governed_rows:
        by_path.setdefault(row["file_path"], []).append(row)

    mapped = []
    for native in native_rows:
        native_path = native.get("path", "")
        normalized_path = native_path if native_path.startswith("/") else str((workspace_root / native_path).resolve())
        candidates = by_path.get(normalized_path, [])
        if not candidates:
            continue
        native_text = native.get("text") or native.get("snippet") or ""
        best = max(candidates, key=lambda item: score(native_text, item.get("raw_text") or item.get("retrieval_text") or ""))
        mapped.append(best)
    deduped = []
    seen = set()
    for row in mapped:
        chunk_id = row["chunk_id"]
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        deduped.append(row)
    return deduped


def decide(query: Dict, memory: Dict) -> Tuple[str, str]:
    purpose = query["purpose"]
    requester_domain = WORKSPACE_DOMAIN.get(query["workspace"], query["workspace"].replace("workspace-", ""))

    if memory["domain"] not in {requester_domain, "shared"}:
        return "deny", "cross_domain"
    if memory["lifecycle"] == "pending_delete":
        return "deny", "pending_delete"
    if memory["privacy_level"] == "L3":
        if "sandbox_only" in memory["purpose_allow"]:
            return "sandbox", "sandbox_only"
        return "downgrade", "high_sensitive"
    if memory["privacy_level"] == "L2":
        if purpose == "external_share":
            return "downgrade", "summary_only"
        return "downgrade", "l2_summary_default"
    if purpose in memory["purpose_allow"]:
        return "allow", "purpose_allowed"
    if purpose == "personalization" and "task_continuity" in memory["purpose_allow"]:
        return "allow", "fallback_task_continuity"
    return "deny", "purpose_not_allowed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Guard OpenClaw memory retrieval with native-index-first fallback.")
    parser.add_argument("--agent", required=True, help="OpenClaw agent id such as main, assistant, code.")
    parser.add_argument("--purpose", required=True, help="Purpose such as task_continuity or external_share.")
    parser.add_argument("--query", required=True, help="User query.")
    parser.add_argument("--workspace", help="Override workspace; defaults from agent id.")
    parser.add_argument("--openclaw-home", default=str(Path.home() / ".openclaw"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--run-id", default="openclaw_guard_demo")
    args = parser.parse_args()

    openclaw_home = Path(args.openclaw_home)
    workspace = args.workspace or WORKSPACE_FOR_AGENT[args.agent]
    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = run_dir / "governed_chunks.jsonl"
    ensure_governed_dataset(dataset_path, openclaw_home)
    governed_rows = load_jsonl(dataset_path)

    query = {
        "query_id": f"{args.run_id}_q001",
        "agent_id": args.agent,
        "workspace": workspace,
        "purpose": args.purpose,
        "query": args.query,
    }

    start = time.perf_counter()
    native_status, native_rows = fetch_native_candidates_via_cli(args.agent, args.query, args.top_k)
    if not native_rows:
        native_status, native_rows = fetch_native_candidates_sqlite(db_path_for_agent(openclaw_home, args.agent), args.query, args.top_k)
    agent_rows = [row for row in governed_rows if row["agent_id"] == args.agent]
    if native_rows:
        workspace_root = openclaw_home / workspace
        candidates = map_native_to_governed(native_rows, agent_rows, workspace_root)
        candidate_source = native_status
    else:
        ranked = []
        for row in agent_rows:
            text = row.get("retrieval_text") or row.get("raw_text") or ""
            match_score = score(args.query, text)
            if match_score > 0:
                ranked.append((match_score, row))
        ranked.sort(key=lambda item: (-item[0], item[1]["chunk_id"]))
        candidates = [item[1] for item in ranked[: args.top_k]]
        candidate_source = f"fallback:{native_status}"

    allowed = []
    denied = []
    downgraded = []
    sandboxed = []
    deny_reasons = {}
    for item in candidates:
        decision, reason = decide(query, item)
        item_id = item["chunk_id"]
        if decision == "allow":
            allowed.append(item)
        elif decision == "deny":
            denied.append(item)
        elif decision == "downgrade":
            downgraded.append(item)
        elif decision == "sandbox":
            sandboxed.append(item)
        deny_reasons[item_id] = reason
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    ts = datetime.now(timezone.utc).isoformat()
    policy_row = {
        "ts": ts,
        "run_id": args.run_id,
        "query_id": query["query_id"],
        "agent_id": args.agent,
        "workspace": workspace,
        "purpose": args.purpose,
        "candidate_source": candidate_source,
        "candidate_chunk_ids": [item["chunk_id"] for item in candidates],
        "allowed_chunk_ids": [item["chunk_id"] for item in allowed],
        "denied_chunk_ids": [item["chunk_id"] for item in denied],
        "downgraded_chunk_ids": [item["chunk_id"] for item in downgraded],
        "sandbox_chunk_ids": [item["chunk_id"] for item in sandboxed],
        "deny_reasons": deny_reasons,
        "policy_eval_latency_ms": latency_ms,
    }
    retrieval_row = {
        "ts": ts,
        "run_id": args.run_id,
        "query_id": query["query_id"],
        "candidate_source": candidate_source,
        "returned_chunk_ids": [item["chunk_id"] for item in allowed + downgraded],
        "returned_domains": [item["domain"] for item in allowed + downgraded],
        "returned_privacy_levels": [item["privacy_level"] for item in allowed + downgraded],
        "raw_exposure": any(item["privacy_level"] in {"L2", "L3"} for item in allowed),
        "downgraded_summary_ids": [item["chunk_id"] for item in downgraded],
    }
    audit_rows = []
    for decision_name, items in [("allow", allowed), ("deny", denied), ("downgrade", downgraded), ("sandbox", sandboxed)]:
        for item in items:
            audit_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "event_type": f"retrieval_{decision_name}",
                    "query_id": query["query_id"],
                    "agent_id": args.agent,
                    "chunk_id": item["chunk_id"],
                    "domain": item["domain"],
                    "privacy_level": item["privacy_level"],
                    "purpose": args.purpose,
                    "decision": decision_name,
                    "reason": deny_reasons[item["chunk_id"]],
                }
            )

    sandbox_rows = [
        {
            "ts": ts,
            "job_id": f"{args.run_id}_{item['chunk_id']}",
            "request_id": query["query_id"],
            "agent_id": args.agent,
            "chunk_id": item["chunk_id"],
            "input_privacy_levels": [item["privacy_level"]],
            "output_mode": "summary_only",
            "raw_output_blocked": True,
            "status": "queued",
        }
        for item in sandboxed
    ]

    response = {
        "query": args.query,
        "agent_id": args.agent,
        "workspace": workspace,
        "purpose": args.purpose,
        "candidate_source": candidate_source,
        "allowed": [
            {
                "chunk_id": item["chunk_id"],
                "privacy_level": item["privacy_level"],
                "text": item.get("raw_text") or item.get("retrieval_text"),
            }
            for item in allowed
        ],
        "downgraded": [
            {
                "chunk_id": item["chunk_id"],
                "privacy_level": item["privacy_level"],
                "summary": summarize_text(item.get("retrieval_text") or item.get("raw_text") or ""),
            }
            for item in downgraded
        ],
        "sandboxed": [
            {
                "chunk_id": item["chunk_id"],
                "privacy_level": item["privacy_level"],
                "status": "queued",
            }
            for item in sandboxed
        ],
        "denied": [
            {
                "chunk_id": item["chunk_id"],
                "privacy_level": item["privacy_level"],
                "reason": deny_reasons[item["chunk_id"]],
            }
            for item in denied
        ],
    }

    write_jsonl(run_dir / "policy_decisions.jsonl", [policy_row])
    write_jsonl(run_dir / "retrieval_hits.jsonl", [retrieval_row])
    write_jsonl(run_dir / "audit_events.jsonl", audit_rows)
    write_jsonl(run_dir / "sandbox_jobs.jsonl", sandbox_rows)
    (run_dir / "response.json").write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
