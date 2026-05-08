#!/usr/bin/env python3

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


def load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def counter_dict(rows: List[Dict], field: str) -> Dict[str, int]:
    return dict(sorted(Counter(row.get(field, "<missing>") for row in rows).items()))


def nested_counter(rows: List[Dict], field_a: str, field_b: str) -> Dict[str, Dict[str, int]]:
    result = {}
    for row in rows:
        key = row.get(field_a, "<missing>")
        result.setdefault(key, Counter())
        result[key][row.get(field_b, "<missing>")] += 1
    return {key: dict(sorted(value.items())) for key, value in sorted(result.items())}


def md_table(headers: List[str], rows: List[List]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def mode(metrics: Dict, name: str) -> Dict:
    return metrics.get("modes", {}).get(name, {})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate report-ready data tables for innovation sharing.")
    parser.add_argument("--run-id", default="report_pack_v1")
    args = parser.parse_args()

    root = Path("experiments")
    run_root = root / "runs"
    out_dir = run_root / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    real_files = load_jsonl(root / "datasets/real_memory_labeled.jsonl")
    real_chunks = load_jsonl(root / "datasets/real_memory_chunks.jsonl")
    real_queries = load_jsonl(root / "datasets/real_chunk_query_set.jsonl")
    attack_queries = load_jsonl(root / "datasets/attack_query_set.jsonl")
    sandbox_queries = load_jsonl(root / "datasets/sandbox_query_set.jsonl")
    sync_queries = load_jsonl(root / "datasets/sync_query_set.jsonl")

    objectization = load_json(run_root / "objectization_eval_v1/metrics.json")
    pre_guard = load_json(run_root / "pre_guard_vs_post_filter_v1/metrics.json")
    output_shape = load_json(run_root / "output_shape_eval_v1/metrics.json")
    local_sync = load_json(run_root / "local_dual_device_sync_v1/metrics.json")
    story_trace = load_json(run_root / "story_trace_v1/metrics.json")
    attack = load_json(run_root / "attack_eval_v1/metrics.json")
    real_baseline = load_json(run_root / "real_chunk_baseline_v1/metrics.json")
    real_guarded = load_json(run_root / "real_chunk_guarded_v2/metrics.json")
    sandbox = load_json(run_root / "sandbox_eval_v1/metrics.json")

    dataset_profile = {
        "real_file_count": len(real_files),
        "real_chunk_count": len(real_chunks),
        "real_query_count": len(real_queries),
        "attack_query_count": len(attack_queries),
        "sandbox_query_count": len(sandbox_queries),
        "sync_query_count": len(sync_queries),
        "chunk_domain_distribution": counter_dict(real_chunks, "domain"),
        "chunk_privacy_distribution": counter_dict(real_chunks, "privacy_level"),
        "chunk_domain_privacy_distribution": nested_counter(real_chunks, "domain", "privacy_level"),
        "real_query_purpose_distribution": counter_dict(real_queries, "purpose"),
        "attack_type_distribution": counter_dict(attack_queries, "attack_type"),
    }

    innovation_evidence = [
        {
            "innovation": "记忆资产化",
            "before": "file_high_privacy_rate=1.0",
            "after": f"chunk_high_privacy_rate={objectization.get('chunk_high_privacy_rate')}",
            "main_metric": f"low_risk_chunk_overprotected_by_file_rate={objectization.get('low_risk_chunk_overprotected_by_file_rate')}",
        },
        {
            "innovation": "记忆防火墙",
            "before": f"post_filter raw_boundary={mode(pre_guard, 'post_filter').get('raw_boundary_exposure_rate')}",
            "after": f"pre_guard raw_boundary={mode(pre_guard, 'pre_guard').get('raw_boundary_exposure_rate')}",
            "main_metric": f"sensitive_raw_exposure={mode(pre_guard, 'pre_guard').get('sensitive_raw_exposure_rate')}",
        },
        {
            "innovation": "可用不可见",
            "before": f"raw exposure={mode(output_shape, 'raw').get('raw_exposure_rate')}",
            "after": f"derived/sandbox exposure={mode(output_shape, 'derived_result').get('raw_exposure_rate')}/{mode(output_shape, 'sandbox_job').get('raw_exposure_rate')}",
            "main_metric": f"derived utility={mode(output_shape, 'derived_result').get('utility_score')}",
        },
        {
            "innovation": "受控流动",
            "before": f"summary stale_recall={mode(local_sync, 'summary_sync').get('stale_recall_count_after_revoke')}",
            "after": f"policy stale_recall={mode(local_sync, 'policy_sync').get('stale_recall_count_after_revoke')}",
            "main_metric": f"policy_gain={mode(local_sync, 'policy_sync').get('personalization_gain')}",
        },
    ]

    attack_summary = {
        "baseline_attack_success_rate": mode(attack, "baseline_raw").get("attack_success_rate"),
        "pre_guard_attack_success_rate": mode(attack, "pre_guard").get("attack_success_rate"),
        "pre_guard_intent_attack_success_rate": mode(attack, "pre_guard_intent").get("attack_success_rate"),
        "pre_guard_intent_allowlist_attack_success_rate": mode(attack, "pre_guard_intent_allowlist").get("attack_success_rate"),
        "baseline_benign_success_rate": mode(attack, "baseline_raw").get("benign_success_rate"),
        "pre_guard_benign_success_rate": mode(attack, "pre_guard").get("benign_success_rate"),
        "pre_guard_intent_benign_success_rate": mode(attack, "pre_guard_intent").get("benign_success_rate"),
        "pre_guard_intent_allowlist_benign_success_rate": mode(attack, "pre_guard_intent_allowlist").get("benign_success_rate"),
        "baseline_raw_sensitive_exposure_rate": mode(attack, "baseline_raw").get("raw_sensitive_exposure_rate"),
        "pre_guard_raw_sensitive_exposure_rate": mode(attack, "pre_guard").get("raw_sensitive_exposure_rate"),
        "pre_guard_intent_raw_sensitive_exposure_rate": mode(attack, "pre_guard_intent").get("raw_sensitive_exposure_rate"),
        "pre_guard_intent_allowlist_raw_sensitive_exposure_rate": mode(attack, "pre_guard_intent_allowlist").get("raw_sensitive_exposure_rate"),
        "attack_query_count": len(attack_queries),
    }

    failure_rows = []
    guarded_retrieval = load_jsonl(run_root / "real_chunk_guarded_v2/retrieval_hits.jsonl")
    query_by_id = {row["query_id"]: row for row in real_queries}
    for row in guarded_retrieval:
        query = query_by_id.get(row["query_id"], {})
        expected_behavior = query.get("expected_behavior", "allow")
        if row.get("raw_exposure"):
            reason = "false_raw_exposure"
        elif expected_behavior.startswith("deny") and not row.get("returned_chunk_ids"):
            reason = "expected_policy_deny"
        elif expected_behavior.startswith("allow") and not row.get("returned_chunk_ids"):
            reason = "false_deny_or_no_candidate"
        elif row.get("downgraded_summary_ids"):
            reason = "downgraded_summary"
        else:
            reason = "normal_allow"
        failure_rows.append(
            {
                "query_id": row["query_id"],
                "expected_behavior": expected_behavior,
                "returned_count": len(row.get("returned_chunk_ids", [])),
                "downgraded_count": len(row.get("downgraded_summary_ids", [])),
                "reason": reason,
            }
        )

    output_failures = []
    output_rows = load_jsonl(run_root / "output_shape_eval_v1/results.jsonl")
    for row in output_rows:
        if row["mode"] in {"deny", "summary", "derived_result", "sandbox_job"} and not row.get("utility_pass"):
            output_failures.append(
                {
                    "query_id": row["query_id"],
                    "mode": row["mode"],
                    "reason": "policy_deny" if row["mode"] == "deny" else "utility_keyword_loss",
                }
            )

    overhead = {
        "real_chunk_baseline_retrieval_p50": real_baseline.get("retrieval_latency_ms_p50"),
        "real_chunk_guarded_retrieval_p50": real_guarded.get("retrieval_latency_ms_p50"),
        "real_chunk_guarded_policy_eval_p50": real_guarded.get("policy_eval_latency_ms_p50"),
        "sandbox_job_overhead_p50": mode(sandbox, "sandbox_job").get("sandbox_overhead_ms_p50"),
        "policy_sync_payload_bytes": mode(local_sync, "policy_sync").get("payload_bytes"),
        "dp_sync_payload_bytes": mode(local_sync, "dp_sync").get("payload_bytes"),
        "dp_sync_epsilon": mode(local_sync, "dp_sync").get("epsilon"),
    }

    pack = {
        "run_id": args.run_id,
        "dataset_profile": dataset_profile,
        "innovation_evidence": innovation_evidence,
        "attack_summary": attack_summary,
        "failure_reason_distribution": dict(Counter(row["reason"] for row in failure_rows)),
        "output_failure_distribution": dict(Counter(row["reason"] for row in output_failures)),
        "overhead": overhead,
        "story_trace": story_trace,
    }

    write_json(out_dir / "summary.json", pack)
    (out_dir / "failure_reasons.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in failure_rows + output_failures),
        encoding="utf-8",
    )

    md = [
        "# 汇报数据包",
        "",
        "## 数据覆盖",
        "",
        md_table(
            ["项目", "数量"],
            [
                ["real files", dataset_profile["real_file_count"]],
                ["real chunks", dataset_profile["real_chunk_count"]],
                ["real chunk queries", dataset_profile["real_query_count"]],
                ["attack queries", dataset_profile["attack_query_count"]],
                ["sandbox queries", dataset_profile["sandbox_query_count"]],
                ["sync queries", dataset_profile["sync_query_count"]],
            ],
        ),
        "",
        "## Chunk 隐私等级分布",
        "",
        md_table(
            ["privacy_level", "count"],
            [[key, value] for key, value in dataset_profile["chunk_privacy_distribution"].items()],
        ),
        "",
        "## 创新点证据表",
        "",
        md_table(
            ["创新点", "Before", "After", "关键指标"],
            [
                [row["innovation"], row["before"], row["after"], row["main_metric"]]
                for row in innovation_evidence
            ],
        ),
        "",
        "## 攻击压力",
        "",
        md_table(
            ["指标", "结果"],
            [[key, value] for key, value in attack_summary.items()],
        ),
        "",
        "## 失败原因",
        "",
        md_table(
            ["reason", "count"],
            [[key, value] for key, value in pack["failure_reason_distribution"].items()],
        ),
        "",
        "## 工程开销",
        "",
        md_table(
            ["指标", "结果"],
            [[key, value] for key, value in overhead.items()],
        ),
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(pack, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
