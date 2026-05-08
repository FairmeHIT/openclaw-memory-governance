# 创新点支撑实验补充

更新日期：2026-04-27

本文档记录为 [`docs/innovation-points.md`](/Users/fairme/Codes/openclaw-personalized-memory/docs/innovation-points.md) 中 4 个故事型创新点补充的实验。补充实验的目的不是替代 release v1 的主结果，而是更直接地回答“这些创新点为什么成立、还能补哪些证据”。

## 1. 实验入口

统一入口：

```bash
make story-evals
```

该命令会生成 5 组 run：

- [`objectization_eval_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/objectization_eval_v1/metrics.json)
- [`pre_guard_vs_post_filter_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/pre_guard_vs_post_filter_v1/metrics.json)
- [`output_shape_eval_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/output_shape_eval_v1/metrics.json)
- [`story_trace_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/story_trace_v1/metrics.json)
- [`local_dual_device_sync_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/local_dual_device_sync_v1/metrics.json)

## 2. 记忆资产化：整文件 vs chunk 对象化

来源：[`objectization_eval_v1/metrics.json`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/objectization_eval_v1/metrics.json)

| 指标 | 结果 |
|---|---:|
| `file_count` | 13 |
| `chunk_count` | 145 |
| `objectization_expansion_ratio` | 11.1538 |
| `metadata_completeness_rate` | 1.0 |
| `file_high_privacy_rate` | 1.0 |
| `chunk_high_privacy_rate` | 0.1586 |
| `low_risk_chunk_overprotected_by_file_rate` | 1.0 |
| `identifier_reduction_rate` | 1.0 |

解释：

- 当前真实文件级样本全部被判为高敏，但 chunk 级只有 `15.86%` 是高敏。
- 如果按整文件治理，所有低风险 chunk 都会被文件级高敏标签过度保护。
- `raw_text/retrieval_text` 分离把显式标识符检出率从 `0.131` 压到 `0.0`。

该实验直接支撑：

> 记忆资产化不是工程洁癖，而是整文件级治理粒度过粗；chunk 对象化能把“普通可用内容”和“高敏控制内容”分离开。

边界：

- 当前只基于本地导出的 13 个真实 OpenClaw 文件和 145 个 chunk。
- 还需要扩大样本，评估不同来源、不同 agent、不同工作区下的稳定性。

## 3. 记忆防火墙：检索前控制 vs 召回后过滤

来源：[`pre_guard_vs_post_filter_v1/metrics.json`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/pre_guard_vs_post_filter_v1/metrics.json)

| 模式 | `task_success_rate` | `raw_boundary_exposure_rate` | `returned_unauthorized_rate` | `sensitive_raw_exposure_rate` | `avg_returned_count` |
|---|---:|---:|---:|---:|---:|
| `baseline_raw` | 1.0 | 0.875 | 0.75 | 0.5 | 5.0 |
| `post_filter` | 0.875 | 0.875 | 0.125 | 0.5 | 3.0 |
| `pre_guard` | 0.875 | 0.125 | 0.125 | 0.0 | 4.375 |

解释：

- `post_filter` 能减少最终返回的越权结果，但不能减少 raw candidate 已经跨过边界的问题。
- `pre_guard` 把敏感原文暴露率压到 `0.0`，同时返回数量高于 `post_filter`。
- 这说明“召回后过滤”和“返回前使用控制”不是等价方案。

该实验直接支撑：

> 记忆防火墙的关键价值，是把控制点放在长期记忆进入模型上下文之前，而不是等内容已经被拿出来以后再补救。

边界：

- 当前是基于本地检索候选的模拟边界暴露评估。
- 后续应补 prompt injection、恶意 third-party query、多 agent 串扰查询集。

## 4. 可用不可见：高敏输出形态矩阵

来源：[`output_shape_eval_v1/metrics.json`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/output_shape_eval_v1/metrics.json)

| 模式 | `task_success_rate` | `utility_score` | `raw_exposure_rate` | `sensitive_leak_rate` | `minimal_output_compliance_rate` |
|---|---:|---:|---:|---:|---:|
| `raw` | 1.0 | 1.0 | 1.0 | 0.5 | 0.0 |
| `deny` | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 |
| `redacted` | 1.0 | 0.8333 | 0.0 | 0.0 | 1.0 |
| `summary` | 1.0 | 1.0 | 0.0 | 0.5 | 0.5 |
| `derived_result` | 1.0 | 0.8333 | 0.0 | 0.0 | 1.0 |
| `sandbox_job` | 1.0 | 0.8333 | 0.0 | 0.0 | 1.0 |

解释：

- `raw` 最有用但不可接受，`deny` 最安全但不可用。
- `summary` 不等于天然安全，如果摘要保留了敏感实体或敏感类别，仍可能泄露。
- `redacted`、`derived_result` 和 `sandbox_job` 在当前样例下能同时保持任务可用和最小必要输出合规。

该实验直接支撑：

> 高敏记忆不是“给或不给”的二选一问题，更关键的是控制输出形态。

边界：

- 当前的 redaction、derived result、sandbox job 都是规则级原型。
- 后续需要真实 sandbox runtime、人工效用评分、敏感泄露人工复核。

## 5. 无真实双设备时的同步测试

如果没有两台真实设备，优先用“单机双设备目录”测试同步语义，而不是直接上 Docker。

新增入口：

```bash
make local-dual-sync-eval
```

来源：[`local_dual_device_sync_v1/metrics.json`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/local_dual_device_sync_v1/metrics.json)

该实验在一个 run 目录下构造两个设备状态：

```text
local_dual_device_sync_v1/
  raw_sync/device_a/
  raw_sync/device_b/
  summary_sync/device_a/
  summary_sync/device_b/
  policy_sync/device_a/
  policy_sync/device_b/
  dp_sync/device_a/
  dp_sync/device_b/
```

每个模式都会写出：

- 初始 device A/B 记忆状态
- 初始同步 payload
- device B 同步后状态
- 撤销 tombstone payload
- device B 撤销后状态
- 查询结果和 stale recall 结果

| 模式 | `task_success_rate_after_initial_sync` | `reidentification_risk_score` | `raw_sensitive_item_count` | `tombstone_count` | `revocation_enforced` | `stale_recall_count_after_revoke` |
|---|---:|---:|---:|---:|---|---:|
| `local_only` | 0.0 | 0.0 | 0 | 0 | true | 0 |
| `raw_sync` | 1.0 | 0.95 | 1 | 0 | false | 1 |
| `summary_sync` | 1.0 | 0.0 | 0 | 0 | false | 1 |
| `policy_sync` | 1.0 | 0.0 | 0 | 1 | true | 0 |
| `dp_sync` | 0.6667 | 0.0 | 0 | 1 | true | 0 |

解释：

- `raw_sync` 个性化收益最高，但带来明显重识别风险，并且撤销后仍能 stale recall。
- `summary_sync` 能把原文风险压到 `0.0`，但如果不带策略元数据和 tombstone，撤销后仍会 stale recall。
- `policy_sync` 在当前样例下保住 `1.0` 任务成功率，同时原文风险为 `0.0`，撤销后不再召回。
- `dp_sync` 风险和撤销控制都成立，但效用下降到 `0.6667`。

该实验直接支撑：

> 受控流动不只是“同步摘要”，还必须同步策略元数据、生命周期和撤销 tombstone；否则脱敏数据仍可能在撤销后继续被召回。

Docker 是否必要：

- **不必要**：如果只验证同步策略、payload 形态、撤销传播、stale recall、重识别风险。
- **有价值**：如果要验证文件系统隔离、网络边界、容器挂载权限、不同运行时之间的数据不可见性。
- **更高阶段**：如果要验证真实手机端或真实 OpenClaw 多 workspace 同步，应再接真实设备或真实客户端。

## 6. 攻击型查询压力测试

新增入口：

```bash
make attack-eval
```

来源：[`attack_eval_v1/metrics.json`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/attack_eval_v1/metrics.json)

攻击集覆盖 10 条查询，包括 prompt injection、跨域召回、第三方导出、metadata exfiltration、role confusion、workspace boundary probe 和 2 条良性保真查询。

| 模式 | `attack_success_rate` | `raw_sensitive_exposure_rate` | `raw_unauthorized_exposure_rate` | `benign_success_rate` |
|---|---:|---:|---:|---:|
| `baseline_raw` | 1.0 | 0.7 | 1.0 | 0.0 |
| `pre_guard` | 0.375 | 0.0 | 0.4 | 0.5 |
| `pre_guard_intent` | 0.0 | 0.0 | 0.1 | 0.5 |
| `pre_guard_intent_allowlist` | 0.0 | 0.0 | 0.0 | 1.0 |

解释：

- `pre_guard` 把攻击型查询下的高敏原文暴露率从 `0.7` 降到 `0.0`。
- `pre_guard` 的攻击成功率仍为 `0.375`，主要来自跨域语义误命中：跨域候选被拦后，系统会回退到同域但不相关的普通记忆。
- `pre_guard_intent` 增加 query intent gate 后，攻击成功率降到 `0.0`，说明“检索前策略 + 查询意图门控”可以补上这类残余攻击面。
- `pre_guard_intent_allowlist` 进一步加入 shared support memory 和意图域过滤后，在当前攻击集上同时实现 `attack_success_rate = 0.0` 与 `benign_success_rate = 1.0`。

汇报时建议这样讲：

> 攻击压力测试不是为了证明系统已经完美，而是为了拆出三层防护收益：策略前置先压住高敏原文泄露，意图门控压住残余跨域攻击，shared allowlist 恢复良性查询保真。

## 7. 汇报数据包

新增入口：

```bash
make report-pack
```

来源：

- Markdown 表格版：[`report_pack_v1/summary.md`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/report_pack_v1/summary.md)
- 结构化 JSON 版：[`report_pack_v1/summary.json`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/report_pack_v1/summary.json)

数据包汇总了写汇报最常用的几张表：

- 数据覆盖：真实文件数、chunk 数、查询集数、攻击查询数
- chunk 隐私等级分布
- 4 个创新点 before/after 证据表
- 攻击压力结果
- 失败原因分布
- 工程开销总览

当前关键摘录：

| 类别 | 指标 | 结果 |
|---|---|---:|
| 数据覆盖 | `real_chunk_count` | 145 |
| 数据覆盖 | `attack_query_count` | 10 |
| 攻击压力 | `pre_guard_attack_success_rate` | 0.375 |
| 攻击压力 | `pre_guard_intent_attack_success_rate` | 0.0 |
| 攻击压力 | `pre_guard_intent_allowlist_benign_success_rate` | 1.0 |
| 攻击压力 | `pre_guard_raw_sensitive_exposure_rate` | 0.0 |
| 工程开销 | `real_chunk_guarded_policy_eval_p50` | 0.011 ms |
| 工程开销 | `sandbox_job_overhead_p50` | 2.518 ms |

## 8. 端到端故事 trace

来源：[`story_trace_v1/metrics.json`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/story_trace_v1/metrics.json)

| 指标 | 结果 |
|---|---:|
| `step_count` | 6 |
| `policy_pass_rate` | 1.0 |
| `raw_exposure_count` | 0 |
| `task_completion_rate` | 1.0 |
| `audit_completeness_rate` | 1.0 |
| `revocation_enforced` | true |

该 trace 串起了一个完整故事：

```text
高敏私人日程产生
  -> 被分类为 L3 personal memory
  -> 工作域请求会议安排
  -> 通过 sandbox/derived result 输出可用时间窗
  -> 第三方请求完整细节被拒绝
  -> 跨设备只同步摘要
  -> 用户撤销后不再召回
```

该实验直接支撑：

> 这套方案不是几个孤立补丁，而是一条从产生、使用、跨域、同步到撤销的记忆治理闭环。

边界：

- 当前是合成故事 trace，用于演示闭环。
- 后续应把 trace 迁移到真实双设备、真实工作域查询和真实撤销链路。

## 9. 对创新点的支撑度更新

| 创新点 | 新增实验后支撑度 | 说明 |
|---|---|---|
| 记忆资产化 | 较强 | 已能证明整文件过粗，chunk 对象化有必要 |
| 记忆防火墙 | 较强 | 已补上 pre-guard vs post-filter 对照和攻击型查询集 |
| 可用不可见 | 较强 | 已补上 raw/deny/redacted/summary/derived/sandbox 矩阵 |
| 受控流动 | 较强 | 已补上单机双设备目录实验，能验证同步 payload、撤销传播和 stale recall |

## 10. 下一步建议

优先补三类更强实验：

1. **强化攻击集**：扩大 prompt injection、多 agent 串扰、第三方诱导导出样本，并拆分 malicious / benign 指标。
2. **产品化意图门控**：将 `pre_guard_intent_allowlist` 从规则原型升级为可配置策略，包括 domain-aware rerank、跨域强 deny 和 shared preference allowlist。
3. **真实隔离执行**：用真实 sandbox runtime 替代规则级 `sandbox_job`。
4. **真实设备或 Docker 隔离同步**：在单机双目录语义成立后，再验证真实隔离边界、网络边界和多轮 DP 预算。
