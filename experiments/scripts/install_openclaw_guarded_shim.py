#!/usr/bin/env python3

import argparse
from pathlib import Path


SCRIPT_TEMPLATE = """#!/bin/sh
exec python3 "{target}" "$@"
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Install a local shim for guarded OpenClaw memory search.")
    parser.add_argument(
        "--target",
        default=str(Path(__file__).resolve().parent / "openclaw_memory_search_guarded.py"),
        help="Path to the guarded search script.",
    )
    parser.add_argument(
        "--output",
        default=str(Path.home() / ".local" / "bin" / "openclaw-memory-search-guarded"),
        help="Output shim path.",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(SCRIPT_TEMPLATE.format(target=str(target)), encoding="utf-8")
    output.chmod(0o755)
    print(output)


if __name__ == "__main__":
    main()
