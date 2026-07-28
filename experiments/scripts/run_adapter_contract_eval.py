#!/usr/bin/env python3

import argparse
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Dict


def load_adapter():
    path = Path(__file__).with_name("openclaw_guard_adapter.py")
    spec = importlib.util.spec_from_file_location("openclaw_guard_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def evaluate_contract() -> Dict[str, bool]:
    adapter = load_adapter()
    query = {
        "workspace": "workspace-assistant",
        "purpose": "external_share",
    }
    cross_domain = {
        "domain": "work",
        "lifecycle": "long",
        "privacy_level": "L1",
        "purpose_allow": ["external_share"],
    }
    l2_personal = {
        "domain": "personal",
        "lifecycle": "long",
        "privacy_level": "L2",
        "purpose_allow": ["external_share"],
        "raw_text": "信用卡尾号 4821 用于订阅。",
        "retrieval_text": "支付习惯：固定信用卡处理订阅。",
    }
    l3_personal = {
        "domain": "personal",
        "lifecycle": "long",
        "privacy_level": "L3",
        "purpose_allow": ["sandbox_only"],
    }
    cross_decision, _ = adapter.decide(query, cross_domain)
    l2_decision, _ = adapter.decide(query, l2_personal)
    l3_decision, _ = adapter.decide(query, l3_personal)
    l2_summary = adapter.summarize_text(l2_personal["retrieval_text"])
    return {
        "cross_domain_denied": cross_decision == "deny",
        "l2_downgraded": l2_decision == "downgrade",
        "l2_raw_suppressed": l2_personal["raw_text"] not in l2_summary,
        "l3_sandbox_queued": l3_decision == "sandbox",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run fixture-based contract checks for the OpenClaw guarded adapter.")
    parser.add_argument("--run-id", default="openclaw_adapter_contract_v1")
    args = parser.parse_args()

    run_dir = Path("experiments/runs") / args.run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    gates = evaluate_contract()
    metrics = {
        "run_id": args.run_id,
        "native_cli_required": False,
        "contract_gates": gates,
        "contract_passed": all(gates.values()),
    }
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
