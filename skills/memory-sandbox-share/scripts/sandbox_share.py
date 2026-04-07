#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_jsonl(path: Path) -> List[Dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_text(text: str, max_len: int = 120) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def safe_output_mode(item: Dict, purpose: str) -> str:
    if item["privacy_level"] == "L3":
        return "summary_only"
    if item["privacy_level"] == "L2" and purpose == "external_share":
        return "summary_only"
    return "deny"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create sandbox/share-safe outputs from sensitive memory chunks.")
    parser.add_argument("--dataset", required=True, help="Governed chunk dataset JSONL.")
    parser.add_argument("--query-id", required=True, help="Query or request identifier.")
    parser.add_argument("--agent-id", required=True, help="Requesting agent id.")
    parser.add_argument("--purpose", required=True, help="Purpose such as external_share.")
    parser.add_argument("--chunk-ids", nargs="+", required=True, help="Chunk IDs to process.")
    parser.add_argument("--output", required=True, help="Output JSONL path for sandbox result records.")
    args = parser.parse_args()

    dataset = {item.get("chunk_id", item["memory_id"]): item for item in load_jsonl(Path(args.dataset))}
    results = []
    for chunk_id in args.chunk_ids:
        item = dataset.get(chunk_id)
        if not item:
            results.append(
                {
                    "job_id": f"{args.query_id}_{chunk_id}",
                    "request_id": args.query_id,
                    "agent_id": args.agent_id,
                    "chunk_id": chunk_id,
                    "status": "missing",
                    "output_mode": "deny",
                    "raw_output_blocked": True,
                    "summary": None,
                }
            )
            continue

        mode = safe_output_mode(item, args.purpose)
        summary = None
        if mode == "summary_only":
            source_text = item.get("retrieval_text") or item.get("raw_text") or item.get("text", "")
            summary = summarize_text(source_text)

        results.append(
            {
                "job_id": f"{args.query_id}_{chunk_id}",
                "request_id": args.query_id,
                "agent_id": args.agent_id,
                "chunk_id": chunk_id,
                "input_privacy_levels": [item["privacy_level"]],
                "output_mode": mode,
                "raw_output_blocked": True,
                "status": "success" if item else "missing",
                "summary": summary,
            }
        )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(results)} sandbox-share records to {out_path}")


if __name__ == "__main__":
    main()
