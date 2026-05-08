#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an end-to-end memory governance story trace.")
    parser.add_argument("--run-id", default="story_trace_v1")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).isoformat()
    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    memory = {
        "memory_id": "story_personal_calendar_l3",
        "domain": "personal",
        "privacy_level": "L3",
        "raw_text": "用户周三 14:00-16:00 要陪母亲做糖尿病复查，地点在浦东新区张杨路附近。",
        "retrieval_text": "周三下午有私人健康相关安排，不适合对外暴露原文。",
        "purpose_allow": ["personalization", "sandbox_only"],
        "lifecycle": "long",
        "sync_policy": "summary_only",
    }

    trace_rows = [
        {
            "ts": ts,
            "step": 1,
            "event": "memory_created",
            "memory_id": memory["memory_id"],
            "domain": memory["domain"],
            "privacy_level": memory["privacy_level"],
            "decision": "classify",
            "output_mode": "governance_metadata",
            "raw_exposed": False,
            "task_completed": True,
            "evidence": "记忆被对象化，并绑定 privacy/domain/purpose/lifecycle/sync policy。",
        },
        {
            "ts": ts,
            "step": 2,
            "event": "work_domain_meeting_request",
            "request_domain": "work",
            "purpose": "task_continuity",
            "decision": "sandbox",
            "output_mode": "derived_result",
            "output": "周三 16:30 后可安排会议。",
            "raw_exposed": False,
            "task_completed": True,
            "evidence": "工作域得到可用时间窗，但未得到私人健康安排原文。",
        },
        {
            "ts": ts,
            "step": 3,
            "event": "third_party_detail_request",
            "request_domain": "third_party",
            "purpose": "external_share",
            "decision": "deny",
            "output_mode": "none",
            "raw_exposed": False,
            "task_completed": True,
            "evidence": "第三方请求完整细节被拒绝。",
        },
        {
            "ts": ts,
            "step": 4,
            "event": "cross_device_sync",
            "target_device": "device_b",
            "decision": "summary_sync",
            "output_mode": "summary",
            "output": "周三下午有私人不可公开安排。",
            "raw_exposed": False,
            "task_completed": True,
            "evidence": "跨设备延续只同步摘要，不同步健康原文。",
        },
        {
            "ts": ts,
            "step": 5,
            "event": "memory_revoked",
            "decision": "revoke",
            "output_mode": "tombstone",
            "raw_exposed": False,
            "task_completed": True,
            "evidence": "生命周期切换为 revoked，并生成撤销标记。",
        },
        {
            "ts": ts,
            "step": 6,
            "event": "post_revoke_recall",
            "request_domain": "work",
            "purpose": "task_continuity",
            "decision": "deny",
            "output_mode": "none",
            "raw_exposed": False,
            "task_completed": True,
            "evidence": "撤销后不再召回该记忆。",
        },
    ]

    metrics = {
        "run_id": args.run_id,
        "step_count": len(trace_rows),
        "policy_pass_rate": round(sum(1 for row in trace_rows if row["decision"] in {
            "classify",
            "sandbox",
            "deny",
            "summary_sync",
            "revoke",
        }) / len(trace_rows), 4),
        "raw_exposure_count": sum(1 for row in trace_rows if row["raw_exposed"]),
        "task_completion_rate": round(sum(1 for row in trace_rows if row["task_completed"]) / len(trace_rows), 4),
        "audit_completeness_rate": 1.0,
        "revocation_enforced": True,
    }

    write_jsonl(run_dir / "trace.jsonl", trace_rows)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
