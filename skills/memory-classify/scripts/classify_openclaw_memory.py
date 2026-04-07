#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List


WORKSPACE_AGENT = {
    "workspace-assistant": "assistant",
    "workspace-main": "main",
    "workspace-code": "code",
    "workspace-content": "content",
    "workspace-zhixi": "zhixi",
}

WORKSPACE_DOMAIN = {
    "workspace-assistant": "personal",
    "workspace-main": "work",
    "workspace-code": "work",
    "workspace-content": "third_party",
    "workspace-zhixi": "personal",
}

TURN_RE = re.compile(r"^(user|assistant):\s*(.*)$", re.IGNORECASE)
MESSAGE_ID_RE = re.compile(r"^\[message_id:.*\]$")
JSON_FENCE_RE = re.compile(r"```json.*?```", re.DOTALL | re.IGNORECASE)
SESSION_META_RE = re.compile(r"^- \*\*(Session Key|Session ID|Source)\*\*:.*$", re.MULTILINE)
SENDER_ID_INLINE_RE = re.compile(r"ou_[a-z0-9]{8,}", re.IGNORECASE)


def list_memory_files(base_dir: Path) -> List[Path]:
    files = []
    for workspace_dir in sorted(base_dir.glob("workspace-*")):
        memory_dir = workspace_dir / "memory"
        if memory_dir.exists():
            files.extend(sorted(memory_dir.glob("*.md")))
    return files


def normalize_retrieval_text(text: str) -> str:
    text = SENDER_ID_INLINE_RE.sub("user", text)
    return re.sub(r"\s+", " ", text).strip()


def build_retrieval_text(text: str) -> str:
    sanitized = JSON_FENCE_RE.sub("", text)
    sanitized = SESSION_META_RE.sub("", sanitized)
    lines = []
    for line in sanitized.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# Session:") or stripped.startswith("## Conversation Summary"):
            continue
        if "untrusted metadata" in stripped.lower():
            continue
        if stripped.startswith("[message_id:"):
            continue
        if stripped.startswith("Sender (untrusted metadata):"):
            continue
        if stripped.startswith("user: Conversation info"):
            continue
        stripped = SENDER_ID_INLINE_RE.sub("user", stripped)
        lines.append(stripped)
    return "\n".join(lines)


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


def classify_chunk(raw_text: str, retrieval_text: str, kind: str, parent: Dict) -> Dict:
    privacy_level = "L0"
    purpose_allow = ["task_continuity"]
    sync_policy = "summary_only"
    index_policy = "full_index"
    lifecycle = "short" if "session-greeting" in parent["file_name"] or "reply-ok" in parent["file_name"] else "mid"

    lower = raw_text.lower()
    if "message_id" in lower or "sender_id" in lower or "session id" in lower:
        privacy_level = "L3"
        purpose_allow = ["sandbox_only"]
        sync_policy = "local_only"
        index_policy = "no_vector_recall"
    elif kind in {"assistant", "user"}:
        privacy_level = "L1"
        purpose_allow = ["task_continuity", "personalization"]
        index_policy = "restricted_index"
    elif "model" in lower or "new session started" in lower or "模型" in raw_text:
        privacy_level = "L2"
        purpose_allow = ["task_continuity", "personalization"]
        index_policy = "restricted_index"

    if any(token in retrieval_text.lower() for token in ["jiutian", "gpt-5.4", "qwen", "模型"]):
        privacy_level = "L2"
        purpose_allow = ["task_continuity", "personalization"]
        index_policy = "restricted_index"

    if parent["domain"] == "third_party" and privacy_level == "L0":
        privacy_level = "L1"

    return {
        "privacy_level": privacy_level,
        "source_trust": "external_import",
        "purpose_allow": purpose_allow,
        "lifecycle": lifecycle,
        "sync_policy": sync_policy,
        "index_policy": index_policy,
    }


def export_file_level(path: Path) -> Dict:
    workspace = path.parents[1].name
    text = path.read_text(encoding="utf-8")
    retrieval_text = build_retrieval_text(text)
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
    return {
        "memory_id": f"real_{digest}",
        "agent_id": WORKSPACE_AGENT.get(workspace, "unknown"),
        "workspace": workspace,
        "domain": WORKSPACE_DOMAIN.get(workspace, "shared"),
        "text": text,
        "retrieval_text": retrieval_text,
        "file_path": str(path),
        "file_name": path.name,
    }


def export_chunk_level(parent: Dict) -> List[Dict]:
    output = []
    for idx, block in enumerate(split_blocks(parent["text"]), start=1):
        raw_text = block["raw_text"].strip()
        if len(raw_text) < 8:
            continue
        chunk_key = hashlib.sha1(f"{parent['memory_id']}::{idx}::{raw_text}".encode("utf-8")).hexdigest()[:16]
        retrieval_text = normalize_retrieval_text(raw_text)
        item = {
            "chunk_id": f"chunk_{chunk_key}",
            "chunk_index": idx,
            "kind": block["kind"],
            "memory_id": parent["memory_id"],
            "agent_id": parent["agent_id"],
            "workspace": parent["workspace"],
            "domain": parent["domain"],
            "file_path": parent["file_path"],
            "file_name": parent["file_name"],
            "raw_text": raw_text,
            "retrieval_text": retrieval_text,
        }
        item.update(classify_chunk(raw_text, retrieval_text, block["kind"], parent))
        output.append(item)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify OpenClaw memory into governed file or chunk records.")
    parser.add_argument("--openclaw-home", default=str(Path.home() / ".openclaw"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=["file", "chunk"], default="chunk")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records: List[Dict] = []
    for path in list_memory_files(Path(args.openclaw_home)):
        parent = export_file_level(path)
        if args.mode == "file":
            parent.update(classify_chunk(parent["text"], parent["retrieval_text"], "file", parent))
            records.append(parent)
        else:
            records.extend(export_chunk_level(parent))

    with out_path.open("w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} {args.mode}-level records to {out_path}")


if __name__ == "__main__":
    main()
