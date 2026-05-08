#!/usr/bin/env python3

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Dict, List


MODES = ["raw", "deny", "redacted", "summary", "derived_result", "sandbox_job"]
SENSITIVE_RE = re.compile(
    r"(\d{6,}|\b\d{4}\b|Palo Alto|BlueHarbor|张杨路|浦东新区|身份证号?|信用卡|病历)",
    re.IGNORECASE,
)


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


def raw_text(item: Dict) -> str:
    return item.get("raw_text") or item.get("text") or item.get("retrieval_text") or ""


def safe_text(item: Dict) -> str:
    return item.get("retrieval_text") or item.get("text") or item.get("raw_text") or ""


def summarize(text: str, max_len: int = 80) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def redact(text: str) -> str:
    return SENSITIVE_RE.sub("[REDACTED]", text)


def derive(text: str) -> str:
    lower = text.lower()
    signals = []
    if "身份证" in text:
        signals.append("证件场景存在，但证件号不输出")
    if "酒店" in text:
        signals.append("可用于酒店入住类提醒")
    if "糖尿病" in text or "复查" in text:
        signals.append("健康提醒：需要定期复查")
    if "blueharbor" in lower or "并购" in text or "收购" in text:
        signals.append("工作机密：仅输出事项类别")
    if "信用卡" in text or "订阅" in text:
        signals.append("支付偏好：固定支付方式处理订阅")
    if "模型" in text or "qwen" in lower or "gpt" in lower:
        signals.append("模型信息：仅输出概括")
    if "偏好" in text or "趋势" in text:
        signals.append("偏好趋势：仅输出聚合摘要")
    return "；".join(signals) or "受控结果：仅输出必要结论"


def keyword_hits(text: str, keywords: List[str]) -> int:
    if not text:
        return 0
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lower)


def leaks_raw_sensitive(text: str) -> bool:
    return bool(SENSITIVE_RE.search(text or ""))


def run_mode(mode: str, query: Dict, items: List[Dict]) -> Dict:
    start = time.perf_counter()
    outputs = []
    raw_exposed = False
    for item in items:
        privacy = item.get("privacy_level", "L0")
        source = raw_text(item)
        safe = safe_text(item)
        if mode == "raw":
            outputs.append(source)
            raw_exposed = raw_exposed or privacy in {"L2", "L3"}
        elif mode == "deny":
            continue
        elif mode == "redacted":
            outputs.append(redact(source))
        elif mode == "summary":
            outputs.append(summarize(safe))
        elif mode == "derived_result":
            outputs.append(derive(source))
        elif mode == "sandbox_job":
            time.sleep(0.002)
            outputs.append("受控分析：" + derive(source))

    returned_text = " ".join(part for part in outputs if part).strip()
    latency_ms = round((time.perf_counter() - start) * 1000, 3)
    utility_hits = keyword_hits(returned_text, query["expected_keywords"])
    utility_pass = utility_hits >= query["utility_min_keywords"]
    minimal_output_compliant = not raw_exposed and not leaks_raw_sensitive(returned_text)
    return {
        "mode": mode,
        "returned_text": returned_text or None,
        "raw_exposed": raw_exposed,
        "leaks_raw_sensitive": leaks_raw_sensitive(returned_text),
        "utility_hit_count": utility_hits,
        "utility_pass": utility_pass,
        "minimal_output_compliant": minimal_output_compliant,
        "latency_ms": latency_ms,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate high-sensitive memory output shapes.")
    parser.add_argument("--sample-dataset", default="experiments/datasets/memory_samples.jsonl")
    parser.add_argument("--real-dataset", default="experiments/datasets/real_memory_chunks.jsonl")
    parser.add_argument("--queries", default="experiments/datasets/sandbox_query_set.jsonl")
    parser.add_argument("--run-id", default="output_shape_eval_v1")
    args = parser.parse_args()

    sample_dataset = {item.get("chunk_id", item["memory_id"]): item for item in load_jsonl(Path(args.sample_dataset))}
    real_dataset = {item.get("chunk_id", item["memory_id"]): item for item in load_jsonl(Path(args.real_dataset))}
    queries = load_jsonl(Path(args.queries))
    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    result_rows = []
    for query in queries:
        dataset = sample_dataset if query["dataset"] == "sample" else real_dataset
        items = [dataset[target_id] for target_id in query["target_ids"] if target_id in dataset]
        for mode in MODES:
            row = run_mode(mode, query, items)
            row.update(
                {
                    "ts": ts,
                    "run_id": args.run_id,
                    "query_id": query["query_id"],
                    "target_ids": query["target_ids"],
                    "purpose": query["purpose"],
                }
            )
            result_rows.append(row)

    metrics = {"run_id": args.run_id, "modes": {}}
    for mode in MODES:
        rows = [row for row in result_rows if row["mode"] == mode]
        count = len(rows) or 1
        latencies = [row["latency_ms"] for row in rows]
        metrics["modes"][mode] = {
            "task_success_rate": round(sum(1 for row in rows if row["returned_text"]) / count, 4),
            "utility_score": round(sum(1 for row in rows if row["utility_pass"]) / count, 4),
            "raw_exposure_rate": round(sum(1 for row in rows if row["raw_exposed"]) / count, 4),
            "sensitive_leak_rate": round(sum(1 for row in rows if row["leaks_raw_sensitive"]) / count, 4),
            "minimal_output_compliance_rate": round(
                sum(1 for row in rows if row["minimal_output_compliant"]) / count,
                4,
            ),
            "latency_ms_p50": round(median(latencies), 3) if latencies else 0.0,
        }

    write_jsonl(run_dir / "results.jsonl", result_rows)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
