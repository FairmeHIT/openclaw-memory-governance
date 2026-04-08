#!/usr/bin/env python3

import argparse
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def score(query: str, text: str) -> int:
    query_terms = Counter(tokenize(query))
    text_terms = Counter(tokenize(text))
    return sum(min(query_terms[token], text_terms[token]) for token in query_terms)


def load_jsonl(path: str) -> List[Dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline retrieval without governance filtering.")
    parser.add_argument("--dataset", default="experiments/datasets/memory_samples.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/query_set.jsonl")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    dataset = load_jsonl(args.dataset)
    queries = load_jsonl(args.queries)
    run_dir = Path("experiments/runs") / args.run_id
    ts = datetime.now(timezone.utc).isoformat()

    retrieval_rows = []
    audit_rows = []
    exposure_rows = []
    for query in queries:
        start = time.perf_counter()
        ranked = []
        for memory in dataset:
            memory_text = memory.get("retrieval_text") or memory.get("raw_text") or memory.get("text", "")
            match_score = score(query["query"], memory_text)
            if match_score > 0:
                ranked.append((match_score, memory))
        ranked.sort(key=lambda item: (-item[0], item[1]["memory_id"]))
        selected = [item[1] for item in ranked[: args.top_k]]
        retrieval_latency_ms = round((time.perf_counter() - start) * 1000, 3)

        retrieval_rows.append(
            {
                "ts": ts,
                "run_id": args.run_id,
                "query_id": query["query_id"],
                "candidate_chunk_ids": [item[1].get("chunk_id", item[1]["memory_id"]) for item in ranked[: args.top_k]],
                "returned_chunk_ids": [item.get("chunk_id", item["memory_id"]) for item in selected],
                "returned_domains": [item["domain"] for item in selected],
                "returned_privacy_levels": [item["privacy_level"] for item in selected],
                "raw_exposure": any(item["privacy_level"] in {"L2", "L3"} for item in selected),
                "retrieval_latency_ms": retrieval_latency_ms,
                "answer_text": " ".join(
                    (item.get("retrieval_text") or item.get("raw_text") or item.get("text") or "").strip()
                    for item in selected
                ).strip() or None,
            }
        )

        for item in selected:
            chunk_id = item.get("chunk_id", item["memory_id"])
            audit_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "event_type": "retrieval_allow",
                    "query_id": query["query_id"],
                    "agent_id": query["agent_id"],
                    "chunk_id": chunk_id,
                    "domain": item["domain"],
                    "privacy_level": item["privacy_level"],
                    "purpose": query["purpose"],
                    "decision": "allow",
                    "reason": "baseline_no_guard",
                }
            )
            if item["privacy_level"] in {"L2", "L3"}:
                exposure_rows.append(
                    {
                        "ts": ts,
                        "run_id": args.run_id,
                        "query_id": query["query_id"],
                        "agent_id": query["agent_id"],
                        "chunk_id": chunk_id,
                        "privacy_level": item["privacy_level"],
                        "domain": item["domain"],
                        "exposure_mode": "raw",
                        "decision": "allow",
                    }
                )

    write_jsonl(run_dir / "retrieval_hits.jsonl", retrieval_rows)
    write_jsonl(run_dir / "audit_events.jsonl", audit_rows)
    write_jsonl(run_dir / "exposures.jsonl", exposure_rows)
    print(f"Baseline run completed: {run_dir}")


if __name__ == "__main__":
    main()
