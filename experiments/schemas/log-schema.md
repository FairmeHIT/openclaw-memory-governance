# Log Schema

所有实验运行建议写入 `experiments/runs/<run_id>/`，并使用 JSONL。

## `policy_decisions.jsonl`

字段：

- `ts`
- `run_id`
- `query_id`
- `agent_id`
- `workspace`
- `purpose`
- `candidate_chunk_ids`
- `allowed_chunk_ids`
- `denied_chunk_ids`
- `downgraded_chunk_ids`
- `sandbox_chunk_ids`
- `deny_reasons`
- `policy_eval_latency_ms`

## `retrieval_hits.jsonl`

字段：

- `ts`
- `run_id`
- `query_id`
- `candidate_chunk_ids`
- `returned_chunk_ids`
- `returned_domains`
- `returned_privacy_levels`
- `raw_exposure`
- `retrieval_latency_ms`
- `answer_text`
- `summary_text`

## `exposures.jsonl`

字段：

- `ts`
- `run_id`
- `query_id`
- `agent_id`
- `chunk_id`
- `privacy_level`
- `domain`
- `exposure_mode`
- `decision`

## `audit_events.jsonl`

字段：

- `ts`
- `run_id`
- `event_type`
- `query_id`
- `agent_id`
- `chunk_id`
- `domain`
- `privacy_level`
- `purpose`
- `decision`
- `reason`
- `latency_ms`
- `sandbox_overhead_ms`

## `metrics.json`

字段建议：

- `task_success_rate`
- `unauthorized_recall_rate`
- `sensitive_raw_exposure_rate`
- `cross_domain_leak_count`
- `policy_enforcement_rate`
- `audit_completeness_rate`
- `answer_quality_score`
- `summary_utility_score`
- `retrieval_latency_ms_p50`
- `retrieval_latency_ms_p95`
- `policy_eval_latency_ms_p50`
- `policy_eval_latency_ms_p95`
- `sandbox_overhead_ms_p50`
- `sandbox_overhead_ms_p95`
