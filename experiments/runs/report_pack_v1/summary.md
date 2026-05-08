# 汇报数据包

## 数据覆盖

| 项目 | 数量 |
| --- | --- |
| real files | 13 |
| real chunks | 145 |
| real chunk queries | 8 |
| attack queries | 10 |
| sandbox queries | 6 |
| sync queries | 3 |

## Chunk 隐私等级分布

| privacy_level | count |
| --- | --- |
| L0 | 64 |
| L1 | 58 |
| L2 | 23 |

## 创新点证据表

| 创新点 | Before | After | 关键指标 |
| --- | --- | --- | --- |
| 记忆资产化 | file_high_privacy_rate=1.0 | chunk_high_privacy_rate=0.1586 | low_risk_chunk_overprotected_by_file_rate=1.0 |
| 记忆防火墙 | post_filter raw_boundary=0.875 | pre_guard raw_boundary=0.125 | sensitive_raw_exposure=0.0 |
| 可用不可见 | raw exposure=1.0 | derived/sandbox exposure=0.0/0.0 | derived utility=0.8333 |
| 受控流动 | summary stale_recall=1 | policy stale_recall=0 | policy_gain=1.0 |

## 攻击压力

| 指标 | 结果 |
| --- | --- |
| baseline_attack_success_rate | 1.0 |
| pre_guard_attack_success_rate | 0.375 |
| pre_guard_intent_attack_success_rate | 0.0 |
| pre_guard_intent_allowlist_attack_success_rate | 0.0 |
| baseline_benign_success_rate | 0.0 |
| pre_guard_benign_success_rate | 0.5 |
| pre_guard_intent_benign_success_rate | 0.5 |
| pre_guard_intent_allowlist_benign_success_rate | 1.0 |
| baseline_raw_sensitive_exposure_rate | 0.7 |
| pre_guard_raw_sensitive_exposure_rate | 0.0 |
| pre_guard_intent_raw_sensitive_exposure_rate | 0.0 |
| pre_guard_intent_allowlist_raw_sensitive_exposure_rate | 0.0 |
| attack_query_count | 10 |

## 失败原因

| reason | count |
| --- | --- |
| normal_allow | 5 |
| downgraded_summary | 2 |
| expected_policy_deny | 1 |

## 工程开销

| 指标 | 结果 |
| --- | --- |
| real_chunk_baseline_retrieval_p50 | 2.224 |
| real_chunk_guarded_retrieval_p50 | 2.409 |
| real_chunk_guarded_policy_eval_p50 | 0.011 |
| sandbox_job_overhead_p50 | 2.518 |
| policy_sync_payload_bytes | 1273 |
| dp_sync_payload_bytes | 1308 |
| dp_sync_epsilon | 2.0 |
