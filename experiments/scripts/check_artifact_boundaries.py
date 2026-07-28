#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List


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


def write_jsonl(path: Path, rows: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def find_raw_replays(text: str, raw_by_id: Dict[str, str], target_ids: List[str]) -> List[str]:
    return [
        memory_id
        for memory_id in target_ids
        if raw_by_id.get(memory_id) and raw_by_id[memory_id] in (text or "")
    ]


def string_values(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from string_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from string_values(child)


def scan_sync_artifact(path: Path, raw_by_id: Dict[str, str]) -> List[Dict]:
    findings = []
    for index, row in enumerate(load_jsonl(path)):
        text = "\n".join(string_values(row))
        matched_ids = find_raw_replays(text, raw_by_id, list(raw_by_id))
        if matched_ids:
            findings.append(
                {
                    "artifact": str(path),
                    "record_index": index,
                    "kind": "sync_payload_raw_l3_replay",
                    "matched_l3_ids": matched_ids,
                }
            )
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan protected sandbox and sync artifacts for complete L3 raw-text replay."
    )
    parser.add_argument("--l3-dataset", default="experiments/datasets/l3_boundary_cases.jsonl")
    parser.add_argument("--sandbox-results", default="experiments/runs/sandbox_eval_v1/results.jsonl")
    parser.add_argument("--sync-run-dir", default="experiments/runs/local_dual_device_sync_v1")
    parser.add_argument("--run-id", default="artifact_boundary_v1")
    args = parser.parse_args()

    l3_cases = load_jsonl(Path(args.l3_dataset))
    raw_by_id = {
        item["memory_id"]: item.get("raw_text") or item.get("text") or ""
        for item in l3_cases
    }
    findings = []
    protected_artifacts = []

    sandbox_path = Path(args.sandbox_results)
    for index, row in enumerate(load_jsonl(sandbox_path)):
        if row.get("mode") != "sandbox_job" or not row.get("contains_l3"):
            continue
        protected_artifacts.append(str(sandbox_path))
        matched_ids = find_raw_replays(
            row.get("returned_text") or "",
            raw_by_id,
            row.get("target_ids", []),
        )
        if matched_ids:
            findings.append(
                {
                    "artifact": str(sandbox_path),
                    "record_index": index,
                    "kind": "sandbox_output_raw_l3_replay",
                    "query_id": row.get("query_id"),
                    "matched_l3_ids": matched_ids,
                }
            )

    sync_dir = Path(args.sync_run_dir)
    for mode in ("policy_sync", "dp_sync"):
        for path in sorted((sync_dir / mode).rglob("*.jsonl")):
            protected_artifacts.append(str(path))
            findings.extend(scan_sync_artifact(path, raw_by_id))

    sandbox_rows = load_jsonl(sandbox_path)
    l3_sandbox_rows = [
        row
        for row in sandbox_rows
        if row.get("mode") == "sandbox_job" and row.get("contains_l3")
    ]
    external_allow_count = sum(
        1
        for row in l3_sandbox_rows
        if row.get("purpose") == "external_share" and row.get("returned_text")
    )
    metrics = {
        "run_id": args.run_id,
        "l3_case_count": len(raw_by_id),
        "protected_artifact_count": len(set(protected_artifacts)),
        "l3_sandbox_output_count": len(l3_sandbox_rows),
        "raw_l3_replay_count": len(findings),
        "external_l3_allow_count": external_allow_count,
        "zero_raw_l3_replay": len(findings) == 0,
        "external_l3_no_output": external_allow_count == 0,
    }
    run_dir = Path("experiments/runs") / args.run_id
    write_jsonl(run_dir / "findings.jsonl", findings)
    write_json(run_dir / "metrics.json", metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
