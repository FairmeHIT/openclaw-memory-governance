# 汇报数据包

## 数据覆盖

| 项目 | 数量 |
| --- | --- |
| real files | 13 |
| real chunks | 145 |
| real chunk queries | 8 |
| attack queries | 18 |
| sandbox queries | 10 |
| L3 cases | 6 |
| L3 queries | 6 |
| sync queries | 4 |

## Chunk 隐私等级分布

| privacy_level | count |
| --- | --- |
| L0 | 64 |
| L1 | 58 |
| L2 | 23 |

## L3 边界覆盖

| 项目 | 数量 |
| --- | --- |
| L3 cases | 6 |
| L3 queries | 6 |
| sandbox queries | 10 |

## 创新点证据表

| 创新点 | Before | After | 关键指标 |
| --- | --- | --- | --- |
| 记忆资产化 | file_high_privacy_rate=1.0 | chunk_high_privacy_rate=0.1586 | low_risk_chunk_overprotected_by_file_rate=1.0 |
| 记忆防火墙 | post_filter raw_boundary=0.875 | pre_guard raw_boundary=0.125 | sensitive_raw_exposure=0.0 |
| 可用不可见 | raw exposure=1.0 | derived/sandbox exposure=0.0/0.0 | derived utility=0.5 |
| 受控流动 | summary stale_recall=1 | policy stale_recall=0 | policy_gain=1.0 |

## 攻击压力

| 指标 | 结果 |
| --- | --- |
| baseline_attack_success_rate | 1.0 |
| pre_guard_attack_success_rate | 0.2143 |
| pre_guard_intent_attack_success_rate | 0.0 |
| pre_guard_intent_allowlist_attack_success_rate | 0.0 |
| baseline_benign_success_rate | 0.0 |
| pre_guard_benign_success_rate | 0.5 |
| pre_guard_intent_benign_success_rate | 0.5 |
| pre_guard_intent_allowlist_benign_success_rate | 1.0 |
| baseline_raw_sensitive_exposure_rate | 0.6111 |
| pre_guard_raw_sensitive_exposure_rate | 0.0 |
| pre_guard_intent_raw_sensitive_exposure_rate | 0.0 |
| pre_guard_intent_allowlist_raw_sensitive_exposure_rate | 0.0 |
| attack_query_count | 18 |

## 失败原因

| reason | count |
| --- | --- |
| normal_allow | 5 |
| downgraded_summary | 2 |
| expected_policy_deny | 1 |

## 工程开销

| 指标 | 结果 |
| --- | --- |
| real_chunk_baseline_retrieval_p50 | 2.167 |
| real_chunk_guarded_retrieval_p50 | 2.258 |
| real_chunk_guarded_policy_eval_p50 | 0.009 |
| sandbox_job_overhead_p50 | 2.518 |
| policy_sync_payload_bytes | 1273 |
| dp_sync_payload_bytes | 1308 |
| dp_sync_epsilon | 2.0 |
| policy_sync_stale_recall_count | 0 |
| policy_sync_revocation_enforced | True |
| sandbox_l3_external_block_rate | 1.0 |
| sandbox_l3_raw_replay_count | 0 |
| artifact_boundary_raw_l3_replay_count | 0 |
| encryption_algorithm | AES-256-GCM |
| encryption_payload_bytes | 1499 |
| encryption_key_source | ephemeral_test_only |
| dual_store_stale_recall_after_tombstone | 0 |
| guarded_retrieval_overhead_p50_ms | 0.091 |

## 验收门槛

| 门槛 | 是否通过 |
| --- | --- |
| guarded_zero_raw_exposure | True |
| guarded_zero_cross_domain_leak | True |
| sandbox_zero_raw_exposure | True |
| sandbox_l3_external_blocked | True |
| sandbox_l3_zero_raw_replay | True |
| policy_sync_zero_stale_recall | True |
| policy_sync_revocation_enforced | True |
| attack_allowlist_zero_attack_success | True |
| attack_allowlist_full_benign_success | True |
| l3_cases_present | True |
| l3_queries_present | True |
| artifact_boundary_zero_raw_l3_replay | True |
| artifact_boundary_external_l3_no_output | True |
| encryption_round_trip | True |
| encryption_tamper_detected | True |
| encryption_no_plaintext | True |
| encryption_key_not_persisted | True |
| encryption_l3_excluded | True |
| dual_store_tombstone_persisted | True |
| dual_store_tombstone_idempotent | True |
| dual_store_no_stale_recall_after_tombstone | True |
| dual_store_late_upsert_blocked | True |
| adapter_contract_passed | True |
| performance_gates_passed | True |
