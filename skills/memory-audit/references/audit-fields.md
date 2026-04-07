# Audit Fields

## `policy_decisions.jsonl`

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

- `query_id`
- `returned_chunk_ids`
- `returned_domains`
- `returned_privacy_levels`
- `raw_exposure`
- `downgraded_summary_ids`

## `audit_events.jsonl`

- `event_type`
- `query_id`
- `agent_id`
- `chunk_id`
- `domain`
- `privacy_level`
- `purpose`
- `decision`
- `reason`
