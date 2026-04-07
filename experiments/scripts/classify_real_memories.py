#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


HIGH_SENSITIVE_PATTERNS = [
    re.compile(r"sender_id"),
    re.compile(r"message_id"),
    re.compile(r"session id", re.IGNORECASE),
    re.compile(r"ou_[a-z0-9]{8,}", re.IGNORECASE),
]

MEDIUM_SENSITIVE_PATTERNS = [
    re.compile(r"model", re.IGNORECASE),
    re.compile(r"source", re.IGNORECASE),
    re.compile(r"timestamp", re.IGNORECASE),
]


def load_jsonl(path: Path) -> List[Dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def classify(item: Dict) -> Dict:
    text = item["text"]
    retrieval_text = item.get("retrieval_text", text)
    lower = text.lower()
    retrieval_lower = retrieval_text.lower()

    privacy_level = "L0"
    source_trust = "external_import"
    lifecycle = "mid"
    sync_policy = "summary_only"
    index_policy = "full_index"
    purpose_allow = ["task_continuity"]

    if any(pattern.search(text) for pattern in HIGH_SENSITIVE_PATTERNS):
        privacy_level = "L3"
        sync_policy = "local_only"
        index_policy = "no_vector_recall"
        purpose_allow = ["sandbox_only"]
        if retrieval_text and not any(pattern.search(retrieval_text) for pattern in HIGH_SENSITIVE_PATTERNS):
            privacy_level = "L2"
            sync_policy = "summary_only"
            index_policy = "restricted_index"
            purpose_allow = ["task_continuity", "personalization"]
    elif any(pattern.search(text) for pattern in MEDIUM_SENSITIVE_PATTERNS):
        privacy_level = "L2"
        sync_policy = "summary_only"
        index_policy = "restricted_index"
        purpose_allow = ["task_continuity", "personalization"]
    elif "你是谁" in retrieval_text or "我是" in retrieval_text:
        privacy_level = "L1"
        purpose_allow = ["task_continuity", "personalization"]

    if "new session started" in lower or "new session started" in retrieval_lower:
        lifecycle = "short"
    if "session greeting" in item["file_name"] or "reply-ok" in item["file_name"]:
        lifecycle = "short"

    item.update(
        {
            "privacy_level": privacy_level,
            "source_trust": source_trust,
            "purpose_allow": purpose_allow,
            "lifecycle": lifecycle,
            "sync_policy": sync_policy,
            "index_policy": index_policy,
        }
    )
    return item


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply heuristic governance labels to exported OpenClaw memories.")
    parser.add_argument(
        "--input",
        default="experiments/datasets/real_memory_samples.jsonl",
        help="Input JSONL path.",
    )
    parser.add_argument(
        "--output",
        default="experiments/datasets/real_memory_labeled.jsonl",
        help="Output labeled JSONL path.",
    )
    args = parser.parse_args()

    items = [classify(item) for item in load_jsonl(Path(args.input))]
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Labeled {len(items)} real memory records into {out_path}")


if __name__ == "__main__":
    main()
