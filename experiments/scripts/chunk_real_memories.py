#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List


TURN_RE = re.compile(r"^(user|assistant):\s*(.*)$", re.IGNORECASE)
MESSAGE_ID_RE = re.compile(r"^\[message_id:.*\]$")


def load_jsonl(path: Path) -> List[Dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def normalize_retrieval_text(text: str) -> str:
    text = re.sub(r"ou_[a-z0-9]{8,}", "user", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_blocks(text: str) -> List[Dict]:
    lines = text.splitlines()
    blocks: List[Dict] = []
    current: List[str] = []
    current_kind = "narrative"

    def flush() -> None:
        nonlocal current, current_kind
        if current:
            raw = "\n".join(current).strip()
            if raw:
                blocks.append({"kind": current_kind, "raw_text": raw})
        current = []
        current_kind = "narrative"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("# Session:") or stripped.startswith("## Conversation Summary"):
            continue
        if stripped.startswith("- **Session Key**") or stripped.startswith("- **Session ID**") or stripped.startswith("- **Source**"):
            continue
        if "untrusted metadata" in stripped.lower():
            flush()
            continue
        if stripped.startswith("```") or stripped.startswith("{") or stripped.startswith("}") or stripped.startswith('"'):
            continue
        if MESSAGE_ID_RE.match(stripped):
            continue

        turn_match = TURN_RE.match(stripped)
        if turn_match:
            role = turn_match.group(1).lower()
            content = turn_match.group(2).strip()
            flush()
            blocks.append({"kind": role, "raw_text": f"{role}: {content}"})
            continue

        if stripped.startswith("- "):
            if current_kind != "list":
                flush()
                current_kind = "list"
            current.append(stripped)
            continue

        if current_kind != "narrative":
            flush()
        current_kind = "narrative"
        current.append(stripped)

    flush()
    return blocks


def classify_chunk(chunk: Dict, parent: Dict) -> Dict:
    raw_text = chunk["raw_text"]
    retrieval_text = normalize_retrieval_text(raw_text)
    privacy_level = "L0"
    purpose_allow = ["task_continuity"]
    sync_policy = "summary_only"
    index_policy = "full_index"

    lower = raw_text.lower()
    if "message_id" in lower or "sender_id" in lower or "session id" in lower:
        privacy_level = "L3"
        purpose_allow = ["sandbox_only"]
        sync_policy = "local_only"
        index_policy = "no_vector_recall"
    elif raw_text.startswith("assistant:") or raw_text.startswith("user:"):
        privacy_level = "L1"
        purpose_allow = ["task_continuity", "personalization"]
        index_policy = "restricted_index"
    elif "model" in lower or "new session started" in lower:
        privacy_level = "L1"
        purpose_allow = ["task_continuity"]
        index_policy = "restricted_index"

    if any(token in retrieval_text.lower() for token in ["jiutian", "gpt-5.4", "qwen", "模型"]):
        privacy_level = max(privacy_level, "L2", key=lambda p: {"L0": 0, "L1": 1, "L2": 2, "L3": 3}[p])
        index_policy = "restricted_index"

    if parent["domain"] == "third_party" and privacy_level == "L0":
        privacy_level = "L1"
        purpose_allow = ["task_continuity"]

    chunk.update(
        {
            "retrieval_text": retrieval_text,
            "privacy_level": privacy_level,
            "source_trust": "external_import",
            "purpose_allow": purpose_allow,
            "lifecycle": "short" if "session-greeting" in parent["file_name"] or "reply-ok" in parent["file_name"] else "mid",
            "sync_policy": sync_policy,
            "index_policy": index_policy,
            "agent_id": parent["agent_id"],
            "workspace": parent["workspace"],
            "domain": parent["domain"],
            "file_path": parent["file_path"],
            "file_name": parent["file_name"],
            "memory_id": parent["memory_id"],
        }
    )
    return chunk


def main() -> None:
    parser = argparse.ArgumentParser(description="Split exported OpenClaw memory files into smaller chunks.")
    parser.add_argument(
        "--input",
        default="experiments/datasets/real_memory_samples.jsonl",
        help="Input exported JSONL path.",
    )
    parser.add_argument(
        "--output",
        default="experiments/datasets/real_memory_chunks.jsonl",
        help="Output chunked JSONL path.",
    )
    args = parser.parse_args()

    parents = load_jsonl(Path(args.input))
    output: List[Dict] = []

    for parent in parents:
        blocks = split_blocks(parent["text"])
        for idx, block in enumerate(blocks, start=1):
            raw_text = block["raw_text"].strip()
            if len(raw_text) < 8:
                continue
            chunk_id = hashlib.sha1(f"{parent['memory_id']}::{idx}::{raw_text}".encode("utf-8")).hexdigest()[:16]
            item = {
                "chunk_id": f"chunk_{chunk_id}",
                "chunk_index": idx,
                "kind": block["kind"],
                "raw_text": raw_text,
            }
            output.append(classify_chunk(item, parent))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for item in output:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {len(output)} chunks to {out_path}")


if __name__ == "__main__":
    main()
