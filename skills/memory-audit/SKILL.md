---
name: memory-audit
description: Record retrieval, denial, downgrade, sandbox, and sharing decisions for governed OpenClaw memory. Use when running privacy experiments, validating exposure metrics, or keeping an execution trail for memory access and sharing behavior.
---

# Memory Audit

Use this skill whenever governed memory decisions need durable evidence.

## Record

Always log:

- query context
- candidate chunks
- final returned chunks
- denied chunks
- downgraded chunks
- sandbox jobs
- policy reasons
- timing

## Recommended Log Files

- `policy_decisions.jsonl`
- `retrieval_hits.jsonl`
- `audit_events.jsonl`
- `sandbox_jobs.jsonl`
- `metrics.json`

## Metrics To Compute

- `task_success_rate`
- `unauthorized_recall_rate`
- `sensitive_raw_exposure_rate`
- `cross_domain_leak_count`
- `policy_enforcement_rate`
- `policy_eval_latency_ms_p50`
- `policy_eval_latency_ms_p95`

## What To Compare

- baseline vs guarded
- file-level vs chunk-level
- raw-return vs summary-first

## Reference

Read [audit-fields.md](./references/audit-fields.md) for the minimal log schema.
