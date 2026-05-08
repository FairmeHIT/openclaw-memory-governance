# 手机智能体长期记忆治理：从可检索上下文到可治理数据资产

更新日期：2026-04-27

建议用途：公司技术分享会正文底稿  
建议时长：25-30 分钟  
配套材料：[PPT 提纲](./tech-sharing-slides.md)、[追问口径](./tech-sharing-qa.md)、[创新点拆分](./innovation-points.md)、[汇报数据包](../experiments/runs/report_pack_v1/summary.md)

## 1. 一句话结论

手机智能体的长期记忆不应该只是“可检索的上下文文件”，而应该升级为一种可治理的数据资产：能分类、能授权、能降级使用、能受控流动、能被审计证明。

更适合作为开场的说法是：

> 当智能体开始长期记住用户，真正的问题不再是“怎么记得更多”，而是“怎么在不失控的前提下记得更久、用得更准、流动得更安全”。

## 2. 背景：记忆能力正在变成治理问题

手机智能体的能力正在从“即时问答”走向“长期个性化服务”。长期个性化依赖记忆：用户偏好、任务习惯、历史决策、工作上下文、跨设备连续状态，都会影响智能体能否真正成为个人助理。

OpenClaw 这类系统把记忆外显化到工作区文件、SQLite/FTS 索引、向量或混合检索链路中。这个设计非常工程化：记忆不再是模型内部不可观察的状态，而是可以保存、切块、索引、召回和审计的对象。

但风险也正来自这里。

当记忆只是一次 prompt 的上下文时，它的生命周期相对短；当记忆变成长期文件和索引时，它就会反复进入未来任务、跨场景使用、跨设备同步，甚至被第三方插件或外部应用间接触达。也就是说：

```text
memory as context
  -> memory as persistent data
  -> memory as governable asset
```

因此，本项目的目标不是重做一个 memory store，而是在 OpenClaw 本地基线上验证一条记忆治理路线：本地优先、策略前置、分层存储、用途约束、审计留痕、跨域受控。

## 3. 核心矛盾：更懂用户 vs 更少暴露用户

长期记忆带来的收益很直接：

- 智能体可以保持任务连续性。
- 智能体可以理解用户偏好和工作习惯。
- 多设备之间可以延续个性化体验。
- 外部工具或第三方应用可以在授权范围内复用部分记忆价值。

但长期记忆也带来四类核心风险：

- **边界不清**：一整份 session 文件里混着普通上下文、身份线索、工作信息和高敏内容。
- **召回失控**：检索系统天然关心相关性，不天然理解场景域、用途和权限。
- **高敏难用**：直接返回原文会泄露，完全拒绝又损失个性化能力。
- **流动扩散**：跨设备、跨应用、第三方接入会把本地风险放大成跨域风险。

所以这里的核心矛盾不是“要不要记忆”，而是：

```text
更懂用户
  vs
更少暴露用户
```

如果只追求记忆能力，系统会变得更聪明但更危险；如果只做简单拦截，系统会更安全但不再个性化。这个项目试图找到中间路线：让记忆参与任务，但每一次使用都带着边界。

## 4. 总体方案

这次分享建议围绕四个创新点展开：

```text
记忆资产化
  -> 记忆防火墙
  -> 可用不可见
  -> 受控流动
  -> 审计可证
```

其中，前四个是主创新点，审计可证是贯穿所有环节的证明体系。

这个顺序不是按现有实验倒推出来的，而是按问题递进组织出来的：

1. 先承认记忆已经成为数据资产，所以要对象化和治理。
2. 对象化之后，召回不能只看相关性，所以要在检索返回前加记忆防火墙。
3. 有了防火墙，高敏记忆不能只有允许/拒绝两种形态，所以要做到可用不可见。
4. 当记忆从单机走向多设备和第三方协作时，原文不能默认流动，所以要受控流动。
5. 最后用审计和实验数据证明每一步是否真的生效。

## 5. 创新点一：记忆资产化

### 定义

记忆资产化，是把记忆从“Markdown 文件 + 检索索引”，升级为带治理属性的记忆对象。

一个可治理记忆对象至少应包含：

- 内容表示：`raw_text`、`retrieval_text`、summary、embedding/index entry
- 风险属性：`privacy_level`
- 场景属性：`domain`
- 用途属性：`purpose_allow`
- 生命周期：`lifecycle`
- 流动策略：`sync_policy`、`index_policy`
- 审计身份：能追踪这条记忆如何被分类、召回、同步和撤销

分享时可以这样讲：

> 不是给文件打标签，而是让每一条可召回的记忆都带着自己的隐私等级、场景域、用途边界和生命周期。

### 解决的问题

整文件治理太粗。真实 OpenClaw session 文件里往往同时包含普通偏好、工作上下文、调试信息、路径线索、个人线索和系统元数据。如果按整文件治理，就会出现两个问题：

- 普通内容被高敏文件标签连带拦截，导致过度保护。
- 高敏片段混在普通文本中，进入索引后难以精确控制。

### 为什么有创新性

它把“记忆管理”从内容工程提升成数据治理问题。

```text
原来：memory = text
现在：memory = content + representation + policy + lifecycle + audit identity
```

这一步是后续能力的基础。没有对象化，就没有细粒度授权、降级输出、受控同步和可验证审计。

### 当前证据

来自 [report_pack_v1](../experiments/runs/report_pack_v1/summary.md)：

| 指标 | 结果 |
|---|---:|
| 真实文件数 | 13 |
| 真实 chunk 数 | 145 |
| 文件级高敏率 | 1.0 |
| chunk 级高敏率 | 0.1586 |
| 元数据完整率 | 1.0 |
| 低风险 chunk 被整文件高敏标签过度保护比例 | 1.0 |

这说明：如果按整文件治理，所有文件都会被判为高敏；但切到 chunk 级后，只有 15.86% 的 chunk 是高敏。记忆资产化不是工程洁癖，而是治理粒度必须从文件级下降到可召回对象级。

### 可量化指标

- `objectization_coverage_rate`
- `metadata_completeness_rate`
- `privacy_level_accuracy`
- `domain_accuracy`
- `high_privacy_false_positive_rate`
- `high_privacy_false_negative_rate`
- `low_risk_chunk_overprotected_by_file_rate`

## 6. 创新点二：记忆防火墙

### 定义

记忆防火墙，是把策略控制放到检索结果返回之前，而不是等敏感内容已经被召回后再过滤。

它要求一次记忆返回同时满足：

- 相关性足够
- 场景域匹配
- 用途被允许
- 隐私等级允许当前返回形态
- 生命周期未撤销
- 高敏对象满足降级或沙箱条件

分享时可以这样讲：

> 传统记忆检索只问“相关不相关”；记忆防火墙要多问一步：“这个场景下该不该被记起？”

### 解决的问题

长期记忆系统最危险的地方，是检索链路天然偏向相关性：

- 工作域提问可能召回个人域记忆。
- 第三方插件请求上下文可能带出长期偏好。
- 一个 agent 的记忆可能被另一个 agent 间接利用。
- Prompt injection 可以诱导系统越过正常任务边界。

这些问题不能稳定依赖“召回后提示模型不要泄露”解决。控制点必须前移到记忆进入模型上下文之前。

### 为什么有创新性

它把 memory search 从“相关性排序”升级成“相关性 + 使用控制”的双阶段系统。

```text
query
  -> candidate retrieval
  -> policy decision
  -> allow / deny / downgrade / sandbox
  -> returned result
```

这里的关键不是多加一个过滤器，而是改变安全边界：敏感原文不应该先跨过边界，再靠后处理补救。

### 当前证据

来自 [pre_guard_vs_post_filter_v1](../experiments/runs/pre_guard_vs_post_filter_v1/metrics.json)：

| 模式 | 任务成功率 | raw boundary 暴露率 | 返回越权率 | 高敏原文暴露率 |
|---|---:|---:|---:|---:|
| `baseline_raw` | 1.0 | 0.875 | 0.75 | 0.5 |
| `post_filter` | 0.875 | 0.875 | 0.125 | 0.5 |
| `pre_guard` | 0.875 | 0.125 | 0.125 | 0.0 |

`post_filter` 能减少最终返回的越权结果，但 raw candidate 已经跨过边界；`pre_guard` 把高敏原文暴露率压到 0.0，同时保持 0.875 的任务成功率。

攻击压力测试进一步说明分层防护的价值：

| 模式 | 攻击成功率 | 高敏原文暴露率 | 良性成功率 |
|---|---:|---:|---:|
| `baseline_raw` | 1.0 | 0.7 | 0.0 |
| `pre_guard` | 0.375 | 0.0 | 0.5 |
| `pre_guard_intent` | 0.0 | 0.0 | 0.5 |
| `pre_guard_intent_allowlist` | 0.0 | 0.0 | 1.0 |

这组数据适合这样解释：策略前置先压住高敏原文泄露，意图门控压住残余跨域攻击，shared allowlist 恢复良性查询保真。

### 可量化指标

- `unauthorized_recall_rate`
- `cross_domain_leak_count`
- `raw_boundary_exposure_rate`
- `sensitive_raw_exposure_rate`
- `attack_success_rate`
- `benign_success_rate`
- `policy_eval_latency_ms_p50/p95`
- `task_success_rate`

## 7. 创新点三：可用不可见

### 定义

可用不可见，是让高敏记忆通过摘要、脱敏、派生结果或受控沙箱参与任务，但不以原文形式暴露给普通上下文、第三方或不匹配场景。

核心不是“高敏记忆一律拒绝”，而是控制输出形态：

```text
低敏：可直接返回
中敏：摘要/脱敏/降级返回
高敏：受控分析，仅输出结果
核心敏感：拒绝或强隔离
```

分享时可以这样讲：

> 高敏记忆可以参与任务，但不必以原文形式被看见。

### 解决的问题

个性化智能体绕不开高敏信息。比如私人日程、长期偏好、健康或财务线索、工作项目上下文，都可能是完成任务所必需的。

如果全部拒绝，智能体会变笨；如果全部返回原文，隐私会失控。所以需要第三条路：记忆参与计算，但只输出最小必要结果。

### 为什么有创新性

它把隐私保护从“访问控制”推进到“使用形态控制”。

这也和可信数据空间里的数据沙箱、隐私计算思想一致：不是让数据自由流动，而是在受控环境中产生合规结果。

### 当前证据

来自 [output_shape_eval_v1](../experiments/runs/output_shape_eval_v1/metrics.json)：

| 模式 | 任务成功率 | 效用分 | 原文暴露率 | 最小必要输出合规率 |
|---|---:|---:|---:|---:|
| `raw` | 1.0 | 1.0 | 1.0 | 0.0 |
| `deny` | 0.0 | 0.0 | 0.0 | 1.0 |
| `redacted` | 1.0 | 0.8333 | 0.0 | 1.0 |
| `summary` | 1.0 | 1.0 | 0.0 | 0.5 |
| `derived_result` | 1.0 | 0.8333 | 0.0 | 1.0 |
| `sandbox_job` | 1.0 | 0.8333 | 0.0 | 1.0 |

这张表有两个重要结论：

- `raw` 可用但不可接受，`deny` 安全但不可用。
- `summary` 不天然安全，摘要如果保留敏感实体或敏感类别，仍可能泄露。

因此，最适合分享的结论是：高敏记忆不是“给不给”的二选一问题，更关键的是“以什么形态参与任务”。

### 可量化指标

- `raw_exposure_rate`
- `sensitive_raw_exposure_rate`
- `sensitive_leak_rate`
- `minimal_output_compliance_rate`
- `summary_utility_score`
- `task_success_rate`
- `sandbox_overhead_ms_p50/p95`

## 8. 创新点四：受控流动

### 定义

受控流动，是让记忆跨设备、跨域、跨主体延续，但默认不让原文自由复制。

同步对象不应只有 raw memory，而应包含：

- summary
- preference signal
- policy metadata
- tombstone
- DP update
- 最小必要的派生结果

分享时可以这样讲：

> 记忆可以延续，但原文不应默认流动。

### 解决的问题

手机智能体最终一定会进入多设备、多应用和第三方协作场景。raw memory 同步虽然直接，但会把风险从单设备扩大到多设备、云端、第三方和办公域：

- 一台设备泄露，变成多端记忆泄露。
- 一个第三方越权，可能接触完整长期偏好。
- 个人域和工作域被同步机制串起来。
- 删除、撤销和生命周期控制变困难。

### 为什么有创新性

它把跨设备同步从“复制数据”改成“同步受控表示”。

```text
不推荐：raw memory everywhere
推荐：summary / preference signal / policy metadata / DP update
```

连续体验来自可控表示的流动，而不是原始记忆的自由复制。

### 当前证据

来自 [local_dual_device_sync_v1](../experiments/runs/local_dual_device_sync_v1/metrics.json)：

| 模式 | 初始同步后任务成功率 | 重识别风险 | 原始高敏条目数 | 撤销是否生效 | 撤销后 stale recall |
|---|---:|---:|---:|---|---:|
| `local_only` | 0.0 | 0.0 | 0 | true | 0 |
| `raw_sync` | 1.0 | 0.95 | 1 | false | 1 |
| `summary_sync` | 1.0 | 0.0 | 0 | false | 1 |
| `policy_sync` | 1.0 | 0.0 | 0 | true | 0 |
| `dp_sync` | 0.6667 | 0.0 | 0 | true | 0 |

这组数据比“summary sync 风险更低”更进一步：summary sync 如果不带策略元数据和 tombstone，撤销后仍可能 stale recall；policy sync 才能同时保留任务成功率、降低原文风险，并阻断撤销后的旧记忆召回。

### 可量化指标

- `task_success_rate_after_initial_sync`
- `personalization_gain`
- `reidentification_risk_score`
- `raw_sensitive_item_count`
- `tombstone_count`
- `revocation_enforced`
- `stale_recall_count_after_revoke`
- `payload_bytes`
- `epsilon`

## 9. 贯穿能力：审计可证

审计不建议作为单独主创新点，但它是让整套方案可信的底座。

每个创新点都需要留下证据：

- 哪条记忆被分类成什么等级。
- 哪次请求为什么被允许、拒绝、降级或送入沙箱。
- 哪条高敏记忆以什么形态返回。
- 哪些对象进入同步。
- 哪些共享被撤销或过期。

可以这样总结：

> 不是只说“我们保护了隐私”，而是能用日志和指标证明每次记忆使用是否符合策略。

当前端到端故事 trace 的指标是：

| 指标 | 结果 |
|---|---:|
| `step_count` | 6 |
| `policy_pass_rate` | 1.0 |
| `raw_exposure_count` | 0 |
| `task_completion_rate` | 1.0 |
| `audit_completeness_rate` | 1.0 |
| `revocation_enforced` | true |

这个 trace 串起了一个完整过程：

```text
高敏私人日程产生
  -> 被分类为 personal high sensitivity memory
  -> 工作域请求会议安排
  -> 通过 sandbox/derived result 输出可用时间窗
  -> 第三方请求完整细节被拒绝
  -> 跨设备只同步摘要和策略
  -> 用户撤销后不再召回
```

## 10. 实验结论如何放进报告

建议不要把分享讲成“我做了很多实验”。实验应服务于故事：

| 创新点 | Before | After | 关键指标 |
|---|---|---|---|
| 记忆资产化 | file 高敏率 1.0 | chunk 高敏率 0.1586 | 整文件治理过度保护比例 1.0 |
| 记忆防火墙 | post-filter raw boundary 0.875 | pre-guard raw boundary 0.125 | 高敏原文暴露 0.0 |
| 可用不可见 | raw exposure 1.0 | derived/sandbox exposure 0.0 | derived utility 0.8333 |
| 受控流动 | summary stale recall 1 | policy stale recall 0 | policy gain 1.0 |

最推荐在主报告里放三张图或表：

1. 四个创新点总览图：资产化 -> 防火墙 -> 可用不可见 -> 受控流动。
2. Before/After 证据表：用 4 行证明每个创新点都有可测收益。
3. 攻击压力表：说明不是只在正常查询上有效，也能面对诱导导出、跨域召回和第三方外传。

## 11. 当前边界

汇报中需要坦诚说明边界，否则容易被追问卡住：

- 当前样本规模仍偏小：真实文件 13 个、真实 chunk 145 个、攻击查询 10 条。
- 当前沙箱是规则级原型，不是真实 TEE 或生产级隔离 runtime。
- 当前 DP 同步是语义验证，不是完整隐私预算管理系统。
- 当前 intent gate 和 allowlist 是原型规则，还需要和真实 OpenClaw hook、真实应用权限、真实用户授权界面结合。
- 当前重点验证治理机制是否成立，不宣称已经形成完整产品级方案。

更稳妥的表达是：

> 这是一套面向长期记忆治理的可验证原型。它证明了关键机制方向有效，但生产化还需要补真实接线、真实沙箱、真实多设备和更大规模样本。

## 12. 下一步

建议按故事线继续补实验和工程集成：

1. 扩大 gold set，验证分类和领域识别在更多真实记忆上的稳定性。
2. 接入真实 OpenClaw memory search hook，减少 wrapper 和模拟层。
3. 补真实 sandbox runtime，对比规则级 sandbox、容器 sandbox、TEE sandbox 的边界和开销。
4. 扩大攻击查询集，覆盖 prompt injection、metadata exfiltration、agent memory bleed、第三方导出、role confusion。
5. 做真实双设备或 Docker 双环境同步测试，验证文件系统隔离、网络边界和撤销传播。
6. 增加人工评分，评估降级输出和派生结果的真实任务效用。

## 13. 结尾

这次项目最核心的价值，不是把某个单点指标做高，而是提出了一条手机智能体长期记忆的治理路线：

```text
先把记忆对象化
再把使用控制前置到检索链路
再用降级输出和受控分析解决高敏记忆可用性
最后用受控同步支持跨设备连续体验
```

最终希望达到的状态是：智能体可以长期记住用户，但每一条记忆都知道自己是谁、能在哪里用、能以什么形态用、能流向哪里、什么时候必须失效，并且这一切都能被审计证明。
