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

JSON_FENCE_RE = re.compile(r"```json.*?```", re.DOTALL | re.IGNORECASE)
SESSION_META_RE = re.compile(r"^- \*\*(Session Key|Session ID|Source)\*\*:.*$", re.MULTILINE)
SENDER_ID_INLINE_RE = re.compile(r"ou_[a-z0-9]{8,}", re.IGNORECASE)


def build_retrieval_text(text: str) -> str:
    sanitized = JSON_FENCE_RE.sub("", text)
    sanitized = SESSION_META_RE.sub("", sanitized)
    lines = []
    for line in sanitized.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# Session:"):
            continue
        if stripped.startswith("## Conversation Summary"):
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


def list_memory_files(base_dir: Path) -> List[Path]:
    files = []
    for workspace_dir in sorted(base_dir.glob("workspace-*")):
        memory_dir = workspace_dir / "memory"
        if memory_dir.exists():
            files.extend(sorted(memory_dir.glob("*.md")))
    return files


def make_record(path: Path) -> Dict:
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
        "notes": "exported_from_openclaw_workspace",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export real OpenClaw memory markdown files as JSONL dataset.")
    parser.add_argument(
        "--openclaw-home",
        default=str(Path.home() / ".openclaw"),
        help="Path to ~/.openclaw",
    )
    parser.add_argument(
        "--output",
        default="experiments/datasets/real_memory_samples.jsonl",
        help="Output JSONL path.",
    )
    args = parser.parse_args()

    base_dir = Path(args.openclaw_home)
    files = list_memory_files(base_dir)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for path in files:
            f.write(json.dumps(make_record(path), ensure_ascii=False) + "\n")

    print(f"Exported {len(files)} OpenClaw memory files to {out_path}")


if __name__ == "__main__":
    main()
