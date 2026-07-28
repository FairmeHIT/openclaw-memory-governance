#!/usr/bin/env python3

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / "experiments" / "runs"
SUMMARY_PATH = RUNS_DIR / "all_experiments_summary.json"


@dataclass(frozen=True)
class Step:
    stage: str
    name: str
    commands: tuple[tuple[str, ...], ...]
    clean_paths: tuple[str, ...] = ()
    required_paths: tuple[str, ...] = ()
    expected_outputs: tuple[str, ...] = ()


def make_command(target: str) -> tuple[str, ...]:
    return ("make", "PYTHON={python}", target)


def python_command(script: str, *args: str) -> tuple[str, ...]:
    return ("{python}", script, *args)


LOCAL_STEPS: tuple[Step, ...] = (
    Step(
        stage="sample",
        name="initialize sample governance db",
        commands=(make_command("init"), make_command("seed")),
        clean_paths=("experiments/governance.sqlite",),
        expected_outputs=("experiments/governance.sqlite",),
    ),
    Step(
        stage="sample",
        name="run sample baseline and guarded experiments",
        commands=(make_command("baseline"), make_command("guarded"), make_command("metrics")),
        clean_paths=("experiments/runs/baseline_v1", "experiments/runs/guarded_v1"),
        expected_outputs=(
            "experiments/runs/baseline_v1/metrics.json",
            "experiments/runs/guarded_v1/metrics.json",
        ),
    ),
    Step(
        stage="real-chunk",
        name="initialize real chunk governance db",
        commands=(make_command("real-chunk-db"),),
        required_paths=("experiments/datasets/real_memory_chunks.jsonl",),
        expected_outputs=("experiments/governance_real_chunks.sqlite",),
    ),
    Step(
        stage="real-chunk",
        name="run real chunk baseline/light/full experiments",
        commands=(
            make_command("real-chunk-baseline"),
            make_command("real-chunk-guarded-light"),
            make_command("real-chunk-guarded"),
            make_command("real-chunk-metrics"),
        ),
        required_paths=(
            "experiments/datasets/real_memory_chunks.jsonl",
            "experiments/datasets/real_chunk_query_set.jsonl",
        ),
        expected_outputs=(
            "experiments/runs/real_chunk_baseline_v1/metrics.json",
            "experiments/runs/real_chunk_guarded_light_v1/metrics.json",
            "experiments/runs/real_chunk_guarded_v2/metrics.json",
        ),
    ),
    Step(
        stage="classifier",
        name="evaluate memory classifier",
        commands=(make_command("classifier-eval"),),
        required_paths=(
            "experiments/datasets/classification_gold.jsonl",
            "experiments/datasets/real_memory_chunks.jsonl",
        ),
        expected_outputs=("experiments/runs/classifier_eval_v2/metrics.json",),
    ),
    Step(
        stage="sandbox",
        name="run high-sensitive sandbox evaluation",
        commands=(make_command("sandbox-eval"),),
        required_paths=(
            "experiments/datasets/memory_samples.jsonl",
            "experiments/datasets/real_memory_chunks.jsonl",
            "experiments/datasets/l3_boundary_cases.jsonl",
            "experiments/datasets/sandbox_query_set.jsonl",
        ),
        expected_outputs=("experiments/runs/sandbox_eval_v1/metrics.json",),
    ),
    Step(
        stage="sync",
        name="run simulated cross-device sync evaluation",
        commands=(make_command("sync-eval"),),
        required_paths=(
            "experiments/datasets/sync_device_a.jsonl",
            "experiments/datasets/sync_device_b.jsonl",
            "experiments/datasets/sync_query_set.jsonl",
        ),
        expected_outputs=("experiments/runs/sync_eval_v1/metrics.json",),
    ),
    Step(
        stage="story",
        name="run story-oriented innovation support experiments",
        commands=(make_command("story-evals"),),
        required_paths=(
            "experiments/datasets/real_memory_labeled.jsonl",
            "experiments/datasets/real_memory_chunks.jsonl",
            "experiments/datasets/real_chunk_query_set.jsonl",
            "experiments/datasets/l3_boundary_cases.jsonl",
            "experiments/datasets/sandbox_query_set.jsonl",
            "experiments/datasets/sync_device_a.jsonl",
            "experiments/datasets/sync_device_b.jsonl",
            "experiments/datasets/sync_query_set.jsonl",
        ),
        expected_outputs=(
            "experiments/runs/objectization_eval_v1/metrics.json",
            "experiments/runs/pre_guard_vs_post_filter_v1/metrics.json",
            "experiments/runs/output_shape_eval_v1/metrics.json",
            "experiments/runs/story_trace_v1/metrics.json",
            "experiments/runs/local_dual_device_sync_v1/metrics.json",
        ),
    ),
    Step(
        stage="attack",
        name="run attack-oriented retrieval evaluation",
        commands=(make_command("attack-eval"),),
        required_paths=(
            "experiments/datasets/attack_query_set.jsonl",
            "experiments/datasets/real_memory_chunks.jsonl",
        ),
        expected_outputs=("experiments/runs/attack_eval_v1/metrics.json",),
    ),
    Step(
        stage="encryption",
        name="validate encrypted-at-rest policy-sync artifact",
        commands=(make_command("encryption-eval"),),
        required_paths=("experiments/datasets/sync_device_a.jsonl",),
        expected_outputs=("experiments/runs/encryption_eval_v1/metrics.json",),
    ),
    Step(
        stage="dual-store",
        name="validate persistent two-store tombstone propagation",
        commands=(make_command("dual-store-sync-eval"),),
        required_paths=(
            "experiments/datasets/sync_device_a.jsonl",
            "experiments/datasets/sync_query_set.jsonl",
        ),
        expected_outputs=("experiments/runs/dual_store_sync_v1/metrics.json",),
    ),
    Step(
        stage="adapter-contract",
        name="run guarded OpenClaw wrapper contract checks",
        commands=(make_command("adapter-contract-eval"),),
        expected_outputs=("experiments/runs/openclaw_adapter_contract_v1/metrics.json",),
    ),
    Step(
        stage="artifact",
        name="scan protected sandbox and sync artifacts",
        commands=(make_command("artifact-boundary-eval"),),
        required_paths=(
            "experiments/datasets/l3_boundary_cases.jsonl",
            "experiments/runs/sandbox_eval_v1/results.jsonl",
            "experiments/runs/local_dual_device_sync_v1/metrics.json",
        ),
        expected_outputs=("experiments/runs/artifact_boundary_v1/metrics.json",),
    ),
    Step(
        stage="performance",
        name="validate prototype latency and artifact-size gates",
        commands=(make_command("performance-gates"),),
        required_paths=(
            "experiments/runs/real_chunk_baseline_v1/metrics.json",
            "experiments/runs/real_chunk_guarded_v2/metrics.json",
            "experiments/runs/sandbox_eval_v1/metrics.json",
            "experiments/runs/encryption_eval_v1/metrics.json",
        ),
        expected_outputs=("experiments/runs/performance_gates_v1/metrics.json",),
    ),
    Step(
        stage="report",
        name="generate report-ready data pack",
        commands=(python_command("experiments/scripts/generate_report_pack.py", "--run-id", "report_pack_v1"),),
        clean_paths=("experiments/runs/report_pack_v1",),
        required_paths=(
            "experiments/runs/objectization_eval_v1/metrics.json",
            "experiments/runs/pre_guard_vs_post_filter_v1/metrics.json",
            "experiments/runs/output_shape_eval_v1/metrics.json",
            "experiments/runs/local_dual_device_sync_v1/metrics.json",
            "experiments/runs/story_trace_v1/metrics.json",
            "experiments/runs/attack_eval_v1/metrics.json",
            "experiments/runs/real_chunk_baseline_v1/metrics.json",
            "experiments/runs/real_chunk_guarded_v2/metrics.json",
            "experiments/runs/real_chunk_guarded_v2/retrieval_hits.jsonl",
            "experiments/runs/sandbox_eval_v1/metrics.json",
            "experiments/runs/artifact_boundary_v1/metrics.json",
            "experiments/runs/encryption_eval_v1/metrics.json",
            "experiments/runs/dual_store_sync_v1/metrics.json",
            "experiments/runs/openclaw_adapter_contract_v1/metrics.json",
            "experiments/runs/performance_gates_v1/metrics.json",
        ),
        expected_outputs=(
            "experiments/runs/report_pack_v1/summary.json",
            "experiments/runs/report_pack_v1/summary.md",
        ),
    ),
)


REFRESH_REAL_DATA_STEPS: tuple[Step, ...] = (
    Step(
        stage="real-data",
        name="refresh real OpenClaw exported/labeled/chunked datasets",
        commands=(make_command("export-real"), make_command("classify-real"), make_command("chunk-real")),
        expected_outputs=(
            "experiments/datasets/real_memory_samples.jsonl",
            "experiments/datasets/real_memory_labeled.jsonl",
            "experiments/datasets/real_memory_chunks.jsonl",
        ),
    ),
)


NATIVE_STEPS: tuple[Step, ...] = (
    Step(
        stage="native",
        name="ensure native OpenClaw FTS indexes",
        commands=(make_command("native-fts-ensure"),),
        expected_outputs=("experiments/runs/native_fts_ensure/summary.json",),
    ),
    Step(
        stage="native",
        name="validate native OpenClaw FTS across agents",
        commands=(make_command("native-fts-validate"),),
        expected_outputs=("experiments/runs/native_fts_validation_v5/metrics.json",),
    ),
)


OPENCLAW_DEMO_STEPS: tuple[Step, ...] = (
    Step(
        stage="openclaw-demo",
        name="run native-first OpenClaw guard adapter demo",
        commands=(make_command("openclaw-guard-demo"),),
        expected_outputs=("experiments/runs/openclaw_guard_native_demo/response.json",),
    ),
    Step(
        stage="openclaw-demo",
        name="run guarded OpenClaw memory search demo",
        commands=(make_command("openclaw-guarded-search-demo"),),
        expected_outputs=("experiments/runs/openclaw_guarded_search_demo/response.json",),
    ),
)


SKILL_DEMO_STEPS: tuple[Step, ...] = (
    Step(
        stage="skill-demo",
        name="run installed skill demos",
        commands=(
            make_command("skill-classify-demo"),
            make_command("skill-guard-demo"),
            make_command("skill-audit-demo"),
            make_command("skill-sandbox-demo"),
        ),
        expected_outputs=(
            "experiments/datasets/generated/skill_chunk_output.jsonl",
            "experiments/runs/skill_guard_demo/retrieval_hits.jsonl",
            "experiments/runs/skill_sandbox_demo/results.jsonl",
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all OpenClaw memory governance experiments from one command."
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable passed into make targets and direct script calls.",
    )
    parser.add_argument(
        "--stage",
        action="append",
        choices=(
            "real-data",
            "sample",
            "real-chunk",
            "classifier",
            "sandbox",
            "sync",
            "story",
            "attack",
            "encryption",
            "dual-store",
            "adapter-contract",
            "artifact",
            "performance",
            "report",
            "native",
            "openclaw-demo",
            "skill-demo",
        ),
        help="Run only the selected stage. Can be provided multiple times.",
    )
    parser.add_argument(
        "--refresh-real-data",
        action="store_true",
        help="Refresh real OpenClaw datasets before experiments. This overwrites generated dataset files.",
    )
    parser.add_argument(
        "--include-native",
        action="store_true",
        help="Include native OpenClaw FTS ensure/validation steps.",
    )
    parser.add_argument(
        "--include-openclaw-demos",
        action="store_true",
        help="Include demos that query the local OpenClaw memory store.",
    )
    parser.add_argument(
        "--include-skill-demos",
        action="store_true",
        help="Include demos that require repo skills installed under ~/.codex/skills.",
    )
    parser.add_argument(
        "--everything",
        action="store_true",
        help="Run local experiments plus native validation, OpenClaw demos, and skill demos.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue after a failed step and report all failures at the end.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved plan without executing commands.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the resolved steps and exit.",
    )
    return parser.parse_args()


def selected_steps(args: argparse.Namespace) -> tuple[Step, ...]:
    all_steps = (
        REFRESH_REAL_DATA_STEPS
        + LOCAL_STEPS
        + NATIVE_STEPS
        + OPENCLAW_DEMO_STEPS
        + SKILL_DEMO_STEPS
    )
    if args.stage:
        selected = frozenset(args.stage)
        return tuple(step for step in all_steps if step.stage in selected)

    return (
        (REFRESH_REAL_DATA_STEPS if args.refresh_real_data else ())
        + LOCAL_STEPS
        + (NATIVE_STEPS if args.include_native or args.everything else ())
        + (OPENCLAW_DEMO_STEPS if args.include_openclaw_demos or args.everything else ())
        + (SKILL_DEMO_STEPS if args.include_skill_demos or args.everything else ())
    )


def command_text(command: Sequence[str], python: str) -> str:
    resolved = tuple(item.replace("{python}", python) for item in command)
    return " ".join(shlex.quote(item) for item in resolved)


def command_for_subprocess(command: Sequence[str], python: str) -> tuple[str, ...]:
    return tuple(item.replace("{python}", python) for item in command)


def path_from_root(path: str) -> Path:
    return ROOT / path


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        return
    if path.exists():
        path.unlink()


def clean_outputs(step: Step) -> None:
    for clean_path in step.clean_paths:
        remove_path(path_from_root(clean_path))


def missing_paths(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(path for path in paths if not path_from_root(path).exists())


def check_required_paths(step: Step) -> None:
    missing = missing_paths(step.required_paths)
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"Missing required input(s) for {step.name}: {joined}")


def run_command(command: Sequence[str], python: str, env: Mapping[str, str]) -> None:
    resolved = command_for_subprocess(command, python)
    subprocess.run(resolved, cwd=ROOT, env=env, check=True)


def status_for_outputs(step: Step) -> dict[str, bool]:
    return {path: path_from_root(path).exists() for path in step.expected_outputs}


def validate_output(path: Path, started_at: float) -> dict[str, object]:
    status: dict[str, object] = {
        "exists": path.exists(),
        "fresh": False,
        "non_empty": False,
        "valid_json": None,
    }
    if not path.exists():
        return status

    stat = path.stat()
    status["fresh"] = stat.st_mtime >= started_at - 1.0
    status["non_empty"] = stat.st_size > 0
    if path.suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
            status["valid_json"] = True
        except json.JSONDecodeError:
            status["valid_json"] = False
    return status


def validate_expected_outputs(step: Step, started_at: float) -> dict[str, dict[str, object]]:
    outputs = {
        path: validate_output(path_from_root(path), started_at)
        for path in step.expected_outputs
    }
    failures = []
    for path, status in outputs.items():
        if not status["exists"]:
            failures.append(f"{path} missing")
        elif not status["non_empty"]:
            failures.append(f"{path} empty")
        elif not status["fresh"]:
            failures.append(f"{path} not updated by this run")
        elif status["valid_json"] is False:
            failures.append(f"{path} is invalid JSON")

    if failures:
        raise RuntimeError("Output validation failed: " + "; ".join(failures))
    return outputs


def write_summary(summary: Mapping) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def print_steps(steps: Sequence[Step], python: str) -> None:
    for index, step in enumerate(steps, start=1):
        print(f"{index}. [{step.stage}] {step.name}")
        for command in step.commands:
            print(f"   $ {command_text(command, python)}")


def run_steps(steps: Sequence[Step], args: argparse.Namespace) -> int:
    env = os.environ.copy()
    env["PYTHON"] = args.python

    started_at = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()
    results = []

    for index, step in enumerate(steps, start=1):
        step_start = time.perf_counter()
        print(f"\n==> [{index}/{len(steps)}] {step.stage}: {step.name}", flush=True)
        try:
            check_required_paths(step)
            clean_outputs(step)
            command_started_at = time.time()
            for command in step.commands:
                print(f"$ {command_text(command, args.python)}", flush=True)
                run_command(command, args.python, env)
            duration_seconds = round(time.perf_counter() - step_start, 3)
            outputs = validate_expected_outputs(step, command_started_at)
            results.append(
                {
                    "stage": step.stage,
                    "name": step.name,
                    "status": "passed",
                    "duration_seconds": duration_seconds,
                    "outputs": outputs,
                }
            )
        except Exception as exc:
            duration_seconds = round(time.perf_counter() - step_start, 3)
            print(f"FAILED: {exc}", file=sys.stderr, flush=True)
            results.append(
                {
                    "stage": step.stage,
                    "name": step.name,
                    "status": "failed",
                    "duration_seconds": duration_seconds,
                    "error": str(exc),
                    "outputs": status_for_outputs(step),
                }
            )
            if not args.continue_on_error:
                break

    failed = tuple(result for result in results if result["status"] != "passed")
    summary = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.perf_counter() - start_time, 3),
        "status": "failed" if failed else "passed",
        "failed_count": len(failed),
        "step_count": len(results),
        "planned_step_count": len(steps),
        "results": results,
    }
    write_summary(summary)

    print(f"\nSummary written to {SUMMARY_PATH.relative_to(ROOT)}")
    if failed:
        print(f"Completed with {len(failed)} failed step(s).", file=sys.stderr)
        return 1
    print("All selected experiments completed successfully.")
    return 0


def main() -> None:
    args = parse_args()
    steps = selected_steps(args)
    if args.list or args.dry_run:
        print_steps(steps, args.python)
        if args.dry_run:
            print("\nDry run only; no commands executed.")
        return
    raise SystemExit(run_steps(steps, args))


if __name__ == "__main__":
    main()
