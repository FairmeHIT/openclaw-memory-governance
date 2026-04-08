#!/usr/bin/env python3

import json
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_NAMES = [
    "memory-classify",
    "memory-guard",
    "memory-audit",
    "memory-sandbox-share",
]


def command_ok(name: str) -> bool:
    return shutil.which(name) is not None


def openclaw_version() -> str:
    if not command_ok("openclaw"):
        return ""
    proc = subprocess.run(
        ["openclaw", "--version"],
        capture_output=True,
        text=True,
    )
    text = (proc.stdout or proc.stderr).strip().splitlines()
    return text[0] if text else ""


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    openclaw_home = Path.home() / ".openclaw"
    results = {
        "python3": command_ok("python3"),
        "openclaw_cli": command_ok("openclaw"),
        "openclaw_version": openclaw_version(),
        "openclaw_home_exists": openclaw_home.exists(),
        "openclaw_memory_dir_exists": (openclaw_home / "memory").exists(),
        "skills_present": {},
    }

    for name in SKILL_NAMES:
        skill_dir = repo_root / "skills" / name
        results["skills_present"][name] = {
            "dir": skill_dir.exists(),
            "skill_md": (skill_dir / "SKILL.md").exists(),
            "agent_yaml": (skill_dir / "agents" / "openai.yaml").exists(),
            "scripts_dir": (skill_dir / "scripts").exists(),
        }

    ok = (
        results["python3"]
        and results["openclaw_cli"]
        and results["openclaw_home_exists"]
        and all(
            all(status.values())
            for status in results["skills_present"].values()
        )
    )
    results["ready_for_local_skill_demo"] = ok
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
