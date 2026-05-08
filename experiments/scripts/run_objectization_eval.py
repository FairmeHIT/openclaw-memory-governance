#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


PRIVACY_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
REQUIRED_FIELDS = [
    "chunk_id",
    "memory_id",
    "raw_text",
    "retrieval_text",
    "privacy_level",
    "domain",
    "purpose_allow",
    "lifecycle",
    "sync_policy",
    "index_policy",
]
IDENTIFIER_RE = re.compile(
    r"(message_id|sender_id|session id|session key|ou_[a-z0-9]+|om_[a-z0-9]+|"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)


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


def rank(level: str) -> int:
    return PRIVACY_RANK.get(level, 0)


def has_identifier(text: str) -> bool:
    return bool(IDENTIFIER_RE.search(text or ""))


def has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value)
    if isinstance(value, list):
        return bool(value)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate file-level memory governance versus chunk-level objectization."
    )
    parser.add_argument("--file-dataset", default="experiments/datasets/real_memory_labeled.jsonl")
    parser.add_argument("--chunk-dataset", default="experiments/datasets/real_memory_chunks.jsonl")
    parser.add_argument("--run-id", default="objectization_eval_v1")
    args = parser.parse_args()

    files = {item["memory_id"]: item for item in load_jsonl(Path(args.file_dataset))}
    chunks = load_jsonl(Path(args.chunk_dataset))
    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    chunks_by_memory = defaultdict(list)
    for chunk in chunks:
        chunks_by_memory[chunk["memory_id"]].append(chunk)

    file_rows = []
    low_chunks = 0
    low_chunks_overprotected_by_file = 0
    high_chunks = 0
    high_chunks_underprotected_by_file = 0
    metadata_complete = 0
    raw_identifier_chunks = 0
    retrieval_identifier_chunks = 0

    for chunk in chunks:
        if all(field in chunk and has_value(chunk[field]) for field in REQUIRED_FIELDS):
            metadata_complete += 1
        if has_identifier(chunk.get("raw_text", "")):
            raw_identifier_chunks += 1
        if has_identifier(chunk.get("retrieval_text", "")):
            retrieval_identifier_chunks += 1

    for memory_id, memory_chunks in sorted(chunks_by_memory.items()):
        file_item = files.get(memory_id)
        if not file_item:
            continue
        file_privacy = file_item.get("privacy_level", "L0")
        file_rank = rank(file_privacy)
        max_chunk_rank = max(rank(chunk["privacy_level"]) for chunk in memory_chunks)
        low_in_file = [chunk for chunk in memory_chunks if rank(chunk["privacy_level"]) <= rank("L1")]
        high_in_file = [chunk for chunk in memory_chunks if rank(chunk["privacy_level"]) >= rank("L2")]
        overprotected = [chunk for chunk in low_in_file if file_rank >= rank("L2")]
        underprotected = [chunk for chunk in high_in_file if file_rank < rank(chunk["privacy_level"])]

        low_chunks += len(low_in_file)
        low_chunks_overprotected_by_file += len(overprotected)
        high_chunks += len(high_in_file)
        high_chunks_underprotected_by_file += len(underprotected)

        file_rows.append(
            {
                "ts": ts,
                "run_id": args.run_id,
                "memory_id": memory_id,
                "file_name": file_item.get("file_name"),
                "workspace": file_item.get("workspace"),
                "domain": file_item.get("domain"),
                "file_privacy_level": file_privacy,
                "max_chunk_privacy_rank": max_chunk_rank,
                "chunk_count": len(memory_chunks),
                "low_risk_chunk_count": len(low_in_file),
                "high_risk_chunk_count": len(high_in_file),
                "low_risk_chunks_overprotected_by_file": len(overprotected),
                "high_risk_chunks_underprotected_by_file": len(underprotected),
            }
        )

    total_chunks = len(chunks) or 1
    total_files = len(files) or 1
    raw_identifier_rate = raw_identifier_chunks / total_chunks
    retrieval_identifier_rate = retrieval_identifier_chunks / total_chunks
    metrics = {
        "run_id": args.run_id,
        "file_count": len(files),
        "chunk_count": len(chunks),
        "objectization_expansion_ratio": round(len(chunks) / total_files, 4),
        "metadata_completeness_rate": round(metadata_complete / total_chunks, 4),
        "file_high_privacy_rate": round(
            sum(1 for item in files.values() if rank(item.get("privacy_level", "L0")) >= rank("L2")) / total_files,
            4,
        ),
        "chunk_high_privacy_rate": round(
            sum(1 for item in chunks if rank(item.get("privacy_level", "L0")) >= rank("L2")) / total_chunks,
            4,
        ),
        "low_risk_chunk_overprotected_by_file_rate": round(
            low_chunks_overprotected_by_file / (low_chunks or 1),
            4,
        ),
        "high_risk_chunk_underprotected_by_file_rate": round(
            high_chunks_underprotected_by_file / (high_chunks or 1),
            4,
        ),
        "raw_identifier_chunk_rate": round(raw_identifier_rate, 4),
        "retrieval_identifier_chunk_rate": round(retrieval_identifier_rate, 4),
        "identifier_reduction_rate": round(
            (raw_identifier_rate - retrieval_identifier_rate) / raw_identifier_rate,
            4,
        )
        if raw_identifier_rate
        else 0.0,
    }

    write_jsonl(run_dir / "file_objectization_details.jsonl", file_rows)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
