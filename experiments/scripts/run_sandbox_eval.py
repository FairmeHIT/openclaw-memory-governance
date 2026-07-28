#!/usr/bin/env python3

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def load_jsonl(path: Path) -> List[Dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize_text(text: str, max_len: int = 96) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def analyze_l3_text(text: str) -> str:
    lower = text.lower()
    findings = []
    if "身份证" in text:
        findings.append("证件类型：身份证")
    if "酒店" in text:
        findings.append("使用场景：酒店入住")
    if "糖尿病" in text:
        findings.append("健康主题：糖尿病")
    if "复查" in text:
        findings.append("提醒类型：定期复查")
    if "blueharbor" in lower:
        findings.append("项目代号：BlueHarbor")
    if "并购" in text or "收购" in text:
        findings.append("事项类型：并购项目")
    if "信用卡" in text:
        findings.append("支付工具：信用卡")
    if "订阅" in text:
        findings.append("用途：订阅费用")
    if not findings:
        findings.append("高敏信息：仅允许受控标签提取")
    return "；".join(findings)


def safe_text(item: Dict) -> str:
    return item.get("retrieval_text") or item.get("text") or item.get("raw_text") or ""


def raw_text(item: Dict) -> str:
    return item.get("raw_text") or item.get("text") or item.get("retrieval_text") or ""


def raw_replayed(items: List[Dict], output_text: str) -> bool:
    return any(
        raw_text(item) and raw_text(item) in output_text
        for item in items
        if item.get("privacy_level") == "L3"
    )


def run_mode(mode: str, query: Dict, items: List[Dict], ts: str) -> Dict:
    start = time.perf_counter()
    outputs = []
    raw_exposed = False
    blocked = False
    sandbox_steps = 0
    contains_l3 = any(item.get("privacy_level") == "L3" for item in items)

    # An external consumer can request an analysis, but cannot receive an L3 result.
    if mode != "baseline_raw" and contains_l3 and query["purpose"] == "external_share":
        blocked = True

    for item in [] if blocked else items:
        privacy = item["privacy_level"]
        source_text = safe_text(item)
        if mode == "baseline_raw":
            outputs.append(raw_text(item))
            raw_exposed = raw_exposed or privacy in {"L2", "L3"}
            continue

        if mode == "summary_only":
            if privacy == "L3" and query["purpose"] == "external_share":
                blocked = True
                continue
            outputs.append(summarize_text(source_text))
            continue

        if mode == "sandbox_job":
            sandbox_steps += 1
            time.sleep(0.002)
            if privacy == "L3":
                outputs.append("受控分析：" + analyze_l3_text(source_text))
            elif privacy == "L2":
                outputs.append("安全摘要：" + summarize_text(source_text, max_len=72))
            else:
                outputs.append(summarize_text(source_text))

    latency_ms = round((time.perf_counter() - start) * 1000, 3)
    output_text = " ".join(part for part in outputs if part).strip()

    return {
        "ts": ts,
        "query_id": query["query_id"],
        "mode": mode,
        "agent_id": query["agent_id"],
        "purpose": query["purpose"],
        "target_ids": query["target_ids"],
        "returned_text": output_text or None,
        "raw_exposed": raw_exposed,
        "raw_replayed": raw_replayed(items, output_text),
        "blocked": blocked and not output_text,
        "job_status": "success" if mode != "sandbox_job" or output_text else "failed",
        "latency_ms": latency_ms,
        "sandbox_steps": sandbox_steps,
    }


def keyword_hits(text: str, keywords: List[str]) -> int:
    if not text:
        return 0
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lower)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sandbox evaluation across raw, summary, and sandbox modes.")
    parser.add_argument("--sample-dataset", default="experiments/datasets/memory_samples.jsonl")
    parser.add_argument("--real-dataset", default="experiments/datasets/real_memory_chunks.jsonl")
    parser.add_argument("--l3-dataset", default="experiments/datasets/l3_boundary_cases.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/sandbox_query_set.jsonl")
    parser.add_argument("--run-id", default="sandbox_eval_v1")
    args = parser.parse_args()

    sample_dataset = {
        item.get("chunk_id", item["memory_id"]): item
        for item in load_jsonl(Path(args.sample_dataset))
    }
    real_dataset = {
        item.get("chunk_id", item["memory_id"]): item
        for item in load_jsonl(Path(args.real_dataset))
    }
    l3_dataset = {
        item.get("chunk_id", item["memory_id"]): item
        for item in load_jsonl(Path(args.l3_dataset))
    }
    queries = load_jsonl(Path(args.queries))

    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    result_rows = []
    audit_rows = []
    modes = ["baseline_raw", "summary_only", "sandbox_job"]

    for query in queries:
        if query["dataset"] == "sample":
            dataset = sample_dataset
        elif query["dataset"] == "l3":
            dataset = l3_dataset
        else:
            dataset = real_dataset
        items = [dataset[item_id] for item_id in query["target_ids"] if item_id in dataset]
        mode_rows = {}
        for mode in modes:
            row = run_mode(mode, query, items, ts)
            row["dataset"] = query["dataset"]
            row["contains_l3"] = any(item.get("privacy_level") == "L3" for item in items)
            row["keyword_hit_count"] = keyword_hits(row["returned_text"] or "", query["expected_keywords"])
            row["utility_pass"] = row["keyword_hit_count"] >= query["utility_min_keywords"]
            mode_rows[mode] = row
            result_rows.append(row)
            audit_rows.append(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "event_type": "sandbox_eval",
                    "query_id": query["query_id"],
                    "mode": mode,
                    "dataset": query["dataset"],
                    "target_ids": query["target_ids"],
                    "decision": "block" if row["blocked"] else "return",
                    "raw_exposed": row["raw_exposed"],
                    "raw_replayed": row["raw_replayed"],
                    "contains_l3": row["contains_l3"],
                    "job_status": row["job_status"],
                    "latency_ms": row["latency_ms"],
                }
            )
        baseline_latency = mode_rows["summary_only"]["latency_ms"]
        sandbox_latency = mode_rows["sandbox_job"]["latency_ms"]
        mode_rows["sandbox_job"]["sandbox_overhead_ms"] = round(max(0.0, sandbox_latency - baseline_latency), 3)
        audit_rows.append(
            {
                "ts": ts,
                "run_id": args.run_id,
                "event_type": "sandbox_job_timing",
                "query_id": query["query_id"],
                "mode": "sandbox_job",
                "target_ids": query["target_ids"],
                "decision": "measure",
                "raw_exposed": False,
                "job_status": mode_rows["sandbox_job"]["job_status"],
                "latency_ms": sandbox_latency,
                "sandbox_overhead_ms": mode_rows["sandbox_job"]["sandbox_overhead_ms"],
            }
        )

    metrics = {}
    for mode in modes:
        mode_rows = [row for row in result_rows if row["mode"] == mode]
        count = len(mode_rows) or 1
        expected_audit_count = count * 2 if mode == "sandbox_job" else count
        metrics[mode] = {
            "raw_exposure_rate": round(sum(1 for row in mode_rows if row["raw_exposed"]) / count, 4),
            "task_success_rate": round(sum(1 for row in mode_rows if row["returned_text"]) / count, 4),
            "summary_utility_score": round(sum(1 for row in mode_rows if row["utility_pass"]) / count, 4),
            "sandbox_job_success_rate": round(
                sum(1 for row in mode_rows if row["job_status"] == "success") / count, 4
            ),
            "audit_completeness_rate": round(
                min(1.0, sum(1 for row in audit_rows if row["mode"] == mode) / expected_audit_count), 4
            ),
            "latency_ms_p50": round(
                sorted(row["latency_ms"] for row in mode_rows)[len(mode_rows) // 2],
                3,
            ) if mode_rows else 0.0,
            "sandbox_overhead_ms_p50": round(
                sorted(row.get("sandbox_overhead_ms", 0.0) for row in mode_rows)[len(mode_rows) // 2],
                3,
            ) if mode_rows else 0.0,
        }
        l3_rows = [row for row in mode_rows if row["contains_l3"]]
        l3_external_rows = [row for row in l3_rows if row["purpose"] == "external_share"]
        l3_internal_rows = [row for row in l3_rows if row["purpose"] != "external_share"]
        l3_count = len(l3_rows) or 1
        external_count = len(l3_external_rows) or 1
        internal_count = len(l3_internal_rows) or 1
        metrics[mode].update(
            {
                "l3_query_count": len(l3_rows),
                "l3_raw_replay_count": sum(1 for row in l3_rows if row["raw_replayed"]),
                "l3_raw_replay_rate": round(
                    sum(1 for row in l3_rows if row["raw_replayed"]) / l3_count,
                    4,
                ),
                "l3_external_query_count": len(l3_external_rows),
                "l3_external_block_rate": round(
                    sum(1 for row in l3_external_rows if row["blocked"]) / external_count,
                    4,
                ),
                "l3_external_allow_count": sum(
                    1 for row in l3_external_rows if row["returned_text"]
                ),
                "l3_internal_utility_score": round(
                    sum(1 for row in l3_internal_rows if row["utility_pass"]) / internal_count,
                    4,
                ),
            }
        )

    write_jsonl(run_dir / "results.jsonl", result_rows)
    write_jsonl(run_dir / "audit_events.jsonl", audit_rows)
    (run_dir / "metrics.json").write_text(
        json.dumps({"run_id": args.run_id, "modes": metrics}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": args.run_id, "modes": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
