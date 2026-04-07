# Policy Reference

## Minimal Rule Matrix

- Same domain + `L0/L1` + normal purpose:
  `allow`
- Same domain + `L2` + normal purpose:
  `downgrade`
- Same domain + `L3` + `sandbox_only`:
  `sandbox`
- Cross domain:
  `deny`
- `shared` domain:
  treat as same domain
- `external_share` + `L2/L3`:
  never raw allow

## Minimal Decision Record

- `query_id`
- `candidate_chunk_ids`
- `allowed_chunk_ids`
- `denied_chunk_ids`
- `downgraded_chunk_ids`
- `sandbox_chunk_ids`
- `deny_reasons`
- `policy_eval_latency_ms`
