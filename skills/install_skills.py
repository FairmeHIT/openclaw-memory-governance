#!/usr/bin/env python3

import argparse
import shutil
from pathlib import Path


SKILL_NAMES = [
    "memory-classify",
    "memory-guard",
    "memory-audit",
    "memory-sandbox-share",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Install repo skills into a local Codex skills directory.")
    parser.add_argument(
        "--target",
        default=str(Path.home() / ".codex" / "skills"),
        help="Target Codex skills directory.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "skills"
    target_root = Path(args.target).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    installed = []
    for name in SKILL_NAMES:
        src = source_root / name
        dst = target_root / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        installed.append(str(dst))

    for path in installed:
        print(path)


if __name__ == "__main__":
    main()
