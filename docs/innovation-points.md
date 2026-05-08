# 技术分享创新点拆分

本文档用于把 [`content.md`](/Users/fairme/Codes/openclaw-personalized-memory/content.md) 中的研究报告，凝练成公司技术分享会可复用的故事线。

这份拆分的优先级是：

```text
创新逻辑 > 故事递进 > 问题解释力 > 可验证性 > 现有实验覆盖度
```

也就是说，创新点不应只从“现在已有哪几组实验”倒推，而应先回答：

- 它解决了手机智能体记忆系统里的什么关键问题
- 它是否带来概念或架构上的跃迁
- 它能否层层递进地讲成一个完整故事
- 它后续能否通过指标和实验验证

已有实验用于支撑和校准这些创新点，但不应该反过来限制创新点的表达。

## 1. 一句话主线

手机智能体的记忆不应该只是“可检索的上下文文件”，而应该被升级为一种 **可治理的数据资产**：能分类、能授权、能降级使用、能受控流动、能被审计证明。

更适合分享开场的讲法：

> 当智能体开始长期记住用户，真正的问题不再是“怎么记得更多”，而是“怎么在不失控的前提下记得更久、用得更准、流动得更安全”。

## 2. 故事冲突

OpenClaw 这类系统把记忆外显化到文件、索引和检索链路中，这是一件很有价值的事：记忆变得可观察、可工程化、可增强。

但它也带来一个根本变化：

```text
记忆不再只是 prompt 的附属品
  -> 记忆变成了会被保存、索引、召回、同步和共享的数据资产
```

一旦记忆成为数据资产，就会出现四个核心问题：

1. **边界不清**：一整份 session 文件里混着普通上下文、身份线索、工作内容和高敏信息。
2. **召回失控**：检索系统只知道相关性，不天然理解场景域、用途和权限。
3. **高敏难用**：直接返回原文会泄露，完全拒绝又损失个性化能力。
4. **流动扩散**：跨设备、跨应用、第三方接入会把本地风险放大成跨域风险。

本项目的故事就是围绕这四个问题逐层推进。

## 3. 推荐核心创新点

建议技术分享主讲 4 个核心创新点，不必面面俱到。

```text
1. 记忆资产化：把记忆从上下文文件变成可治理对象
2. 记忆防火墙：把使用控制前置到检索返回之前
3. 可用不可见：让高敏记忆通过降级和受控计算发挥价值
4. 受控流动：让记忆跨设备/跨域延续，但不原文裸奔
```

审计、指标、实验不作为单独主创新点，而作为贯穿全程的证明体系。

## 4. 创新点一：记忆资产化

### 这个点要讲什么

把 OpenClaw 的记忆从“Markdown 文件 + 检索索引”，抽象成带治理属性的记忆对象。

实现上可以落到 chunk，但分享时不要一开始就陷入 chunk 细节。更有冲击力的表达是：

> 不是给文件打标签，而是让每一条可召回的记忆都带着自己的隐私等级、场景域、用途边界和生命周期。

### 解决的问题

整文件治理太粗，会产生两个后果：

- 普通内容和敏感内容混在一起，导致要么过度拦截，要么过度暴露。
- 记忆一旦进入索引，就只剩“相关不相关”，缺少“该不该用、在哪里用、能用多久”的治理语义。

### 眼前一亮的地方

它把“记忆管理”从内容工程提升成数据治理问题。

```text
原来：memory = text
现在：memory = content + representation + policy + lifecycle + audit identity
```

这一步是后面所有能力的基础。没有对象化，就没有细粒度授权、降级输出、受控同步和可验证审计。

### 可定义

一个可治理记忆对象至少包含：

- 内容表示：`raw_text`、`retrieval_text`、summary、embedding/index entry
- 风险属性：`privacy_level`
- 场景属性：`domain`
- 用途属性：`purpose_allow`
- 生命周期：`lifecycle`
- 流动策略：`sync_policy`、`index_policy`

### 可量化

建议指标：

- 记忆对象覆盖率：多少原始记忆被成功对象化
- 元数据完整率：每个对象是否具备必要治理字段
- 分类准确率：`privacy_level_accuracy`
- 场景识别准确率：`domain_accuracy`
- 过度高敏化率：普通内容被错误打成高敏的比例
- 高敏漏标率：敏感内容未被识别的比例

### 可验证

现有实验可以作为初步支撑：

- [`classifier_eval_v2`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/classifier_eval_v2/metrics.json)
- 真实 OpenClaw memory chunk 数据

后续可补实验：

- 扩大 gold set
- 增加跨主题、跨 agent、跨工作区样本
- 专门评测“整文件治理 vs chunk 对象化治理”的误杀和漏放差异

## 5. 创新点二：记忆防火墙

### 这个点要讲什么

把策略控制放到检索结果返回之前，而不是等敏感内容已经被召回后再做补救。

可以用一个容易懂的比喻：

> 传统记忆检索像搜索引擎，只问“相关不相关”；记忆防火墙要多问一步：“这个场景下该不该被记起？”

### 解决的问题

智能体记忆系统最危险的地方之一，是召回链路天然偏向相关性：

- 用户在工作域提问，系统可能召回个人域记忆。
- 第三方插件请求上下文，系统可能带出不该给第三方看的长期偏好。
- 一个 agent 的记忆可能被另一个 agent 间接利用。

这些问题不是靠“召回后提示模型不要泄露”能稳定解决的，控制点必须前移。

### 眼前一亮的地方

它把 memory search 从“相关性排序”升级为“相关性 + 使用控制”的双阶段系统。

```text
query
  -> candidate retrieval
  -> policy decision
  -> allow / deny / downgrade / sandbox
  -> returned result
```

这相当于在智能体的长期记忆和模型上下文之间加了一层记忆防火墙。

### 可定义

一次记忆返回必须同时满足：

- 相关性足够
- 场景域匹配
- 用途被允许
- 隐私等级允许当前返回形态
- 生命周期未撤销
- 高敏对象满足降级或沙箱条件

### 可量化

建议指标：

- `unauthorized_recall_rate`
- `cross_domain_leak_count`
- `policy_enforcement_rate`
- `policy_eval_latency_ms_p50/p95`
- 正常任务成功率：`task_success_rate`
- 检索质量：`answer_quality_score`

### 可验证

现有实验可以初步支撑：

- [`real_chunk_baseline_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/real_chunk_baseline_v1/metrics.json)
- [`real_chunk_guarded_v2`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/real_chunk_guarded_v2/metrics.json)

后续可补实验：

- 多 agent 记忆串扰测试
- personal/work/third-party 三域混合查询集
- prompt injection 诱导跨域召回测试
- 检索前控制 vs 召回后过滤对照实验

## 6. 创新点三：可用不可见

### 这个点要讲什么

高敏记忆不是只能“返回原文”或“完全拒绝”。更好的方式是按风险等级改变使用形态：

- L1/L2：摘要优先、字段脱敏、受限返回
- L3：进入受控分析或沙箱，只输出最小必要结果

核心表达：

> 高敏记忆可以参与任务，但不必以原文形式暴露。

### 解决的问题

个性化智能体绕不开高敏信息。比如：

- 用户习惯
- 私人日程
- 健康或财务线索
- 工作项目上下文
- 长期偏好和决策模式

如果全部拒绝，智能体会变笨；如果全部返回原文，隐私会失控。这里需要一个中间层：让记忆可用，但不可直接看见。

### 眼前一亮的地方

它把隐私保护从“访问控制”推进到“使用形态控制”。

```text
低敏：可直接返回
中敏：摘要/脱敏/降级返回
高敏：受控分析，仅输出结果
核心敏感：拒绝或强隔离
```

这也是和可信数据空间最容易建立联系的一点：不是数据自由流动，而是在受控环境里产生合规结果。

### 可定义

对每个隐私等级定义允许输出形态：

- `raw`
- `summary`
- `redacted`
- `derived_result`
- `sandbox_job`
- `deny`

输出策略不是模型临场决定，而是由记忆对象的等级、用途、场景域和生命周期共同决定。

### 可量化

建议指标：

- `sensitive_raw_exposure_rate`
- `raw_exposure_rate`
- `summary_utility_score`
- `task_success_rate`
- `sandbox_overhead_ms_p50/p95`
- 最小必要输出合规率

### 可验证

现有实验可以初步支撑：

- [`real_chunk_guarded_light_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/real_chunk_guarded_light_v1/metrics.json)
- [`real_chunk_guarded_v2`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/real_chunk_guarded_v2/metrics.json)
- [`sandbox_eval_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/sandbox_eval_v1/metrics.json)

后续可补实验：

- 摘要质量分层评测
- L2 summary vs L2 redaction vs L2 raw 对照
- 真实 sandbox runtime 对照
- 高敏任务中“结果可用性”和“原文暴露率”的联合评估

## 7. 创新点四：受控流动

### 这个点要讲什么

手机智能体一定会走向多设备、多应用和第三方协作。问题不是“要不要同步记忆”，而是“同步什么形态的记忆”。

核心表达：

> 记忆可以延续，但原文不应默认流动。

### 解决的问题

raw memory 同步虽然最直接，但会把风险从单设备扩大到多设备、云端、第三方和办公域：

- 一台设备泄露，变成多端记忆泄露。
- 一个第三方插件越权，可能接触完整长期偏好。
- 个人域和工作域被同步机制串起来。
- 删除、撤销和生命周期控制变困难。

### 眼前一亮的地方

它把跨设备同步从“复制数据”改成“同步受控表示”。

```text
不推荐：raw memory everywhere
推荐：summary / preference signal / policy metadata / DP update
```

也就是说，连续体验来自可控表示的流动，而不是原始记忆的自由复制。

### 可定义

按隐私等级定义同步策略：

- L0：可同步低风险表示
- L1：可同步摘要或偏好标签
- L2：默认不同步原文，只同步最小必要摘要或受控统计
- L3：默认不进入普通同步链路，只允许本地优先或强隔离路径

### 可量化

建议指标：

- `personalization_gain`
- `task_success_rate`
- `reidentification_risk_score`
- `raw_sensitive_item_count`
- `payload_bytes`
- `sync_overhead_ms_p50/p95`
- DP 路线中的 `epsilon`

### 可验证

现有实验可以初步支撑：

- [`sync_eval_v1`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/sync_eval_v1/metrics.json)

后续可补实验：

- 真实双设备同步
- 多轮同步后的隐私预算累计
- 重识别攻击评测
- raw sync vs summary sync vs DP sync 在更多任务集上的效用对照

## 8. 贯穿能力：审计可证

审计不建议作为主创新点单独讲，但它是让整个故事可信的底座。

每个创新点都需要能留下证据：

- 哪条记忆被分类成什么等级
- 哪次请求为什么被允许或拒绝
- 哪条高敏记忆以什么形态返回
- 哪些对象进入同步
- 哪些共享被撤销或过期

这对应一个更强的表达：

> 不是只说“我们保护了隐私”，而是能用日志和指标证明每次记忆使用是否符合策略。

建议指标：

- `audit_completeness_rate`
- policy decision 覆盖率
- 共享/撤销日志完整率
- 策略版本可追溯率

## 9. 当前补充实验支撑

新增故事导向实验入口：

```bash
make story-evals
```

生成汇报表格入口：

```bash
make report-pack
```

补充实验详见 [`innovation-support-experiments.md`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/reports/innovation-support-experiments.md)。

当前支撑关系：

| 创新点 | 新增实验 | 能证明什么 |
|---|---|---|
| 记忆资产化 | `objectization_eval_v1` | 整文件治理过粗，chunk 对象化能降低过度高敏化 |
| 记忆防火墙 | `pre_guard_vs_post_filter_v1` | 检索前控制和召回后过滤不是等价方案 |
| 可用不可见 | `output_shape_eval_v1` | 高敏记忆应控制输出形态，而不是只做允许/拒绝 |
| 受控流动 | `local_dual_device_sync_v1` + `story_trace_v1` | 原文不流动也能保留连续体验，并验证撤销传播和 stale recall |

最适合放进分享的数据：

- 文件级高敏率 `1.0`，chunk 级高敏率 `0.1586`，说明整文件治理明显过粗。
- `post_filter` 的 raw boundary 暴露率仍为 `0.875`，`pre_guard` 降到 `0.125`，说明控制点前置有独立价值。
- 高敏输出矩阵中，`raw` 可用但暴露，`deny` 安全但不可用，`derived_result/sandbox_job` 能做到原文不暴露且任务可完成。
- 本地双设备实验中，`summary_sync` 风险为 `0.0` 但撤销后仍 stale recall，`policy_sync` 同样保留 `1.0` 任务成功率且撤销后不再召回。
- 攻击型查询中，`pre_guard` 把高敏原文暴露率压到 `0.0`；加入 `pre_guard_intent` 后攻击成功率从 `0.375` 降到 `0.0`；再加入 `pre_guard_intent_allowlist` 后良性保真从 `0.5` 提升到 `1.0`。

## 10. 推荐 PPT 页结构

### 第 1 页：开场问题

手机智能体越懂用户，越依赖长期记忆。但长期记忆一旦可保存、可索引、可召回、可同步，就不再只是上下文，而是高价值个人数据资产。

### 第 2 页：核心矛盾

```text
更懂用户
  vs
更少暴露用户
```

传统做法容易落入两端：

- 只追求记忆能力：风险失控
- 只做简单拦截：个性化下降

### 第 3 页：总方案

```text
记忆资产化
  -> 记忆防火墙
  -> 可用不可见
  -> 受控流动
  -> 审计可证
```

### 第 4 页：创新点一

记忆资产化：从上下文文件到可治理对象。

重点讲：

- 记忆对象不等于原文
- 每条记忆带隐私等级、场景域、用途、生命周期
- chunk 是工程实现，不是故事终点

### 第 5 页：创新点二

记忆防火墙：从召回后过滤到检索前使用控制。

重点讲：

- 相关不等于可用
- 检索返回前做 allow / deny / downgrade / sandbox
- 解决跨域串扰和越权召回

### 第 6 页：创新点三

可用不可见：高敏记忆通过摘要、脱敏、沙箱参与任务。

重点讲：

- 不在“原文返回”和“完全拒绝”之间二选一
- 高敏记忆可以参与计算，但只输出最小必要结果
- 和可信数据空间的数据沙箱思想呼应

### 第 7 页：创新点四

受控流动：跨设备同步摘要、偏好表示或 DP 更新，而不是同步原文。

重点讲：

- 连续体验不等于 raw memory everywhere
- 多端同步要按隐私等级和用途分层
- summary sync / DP sync 是不同隐私效用折中

### 第 8 页：证据页

把已有实验作为证据，而不是作为创新点来源。

建议只放 2-3 个最关键结果：

- 跨域串扰从 `4` 到 `0`
- 高敏原文暴露率从 `0.25` 到 `0.0`
- summary/sandbox 路线在降低暴露的同时保留可用性

### 第 9 页：边界与下一步

坦诚说明：

- 当前是治理层原型，不是生产级完整系统
- 真实 OpenClaw 内部 hook、真实 sandbox、真实双设备同步仍需补
- 后续实验应围绕四个创新点补齐，而不是为了已有实验反向定义创新点

## 11. 对外表达注意事项

建议强调：

- 这是从“记忆能力”走向“记忆治理能力”的方案
- 创新点按问题和架构递进组织，不是按实验表格组织
- 实验用于证明关键机制方向有效，后续还可以继续补强

避免过度表述：

- 不说“彻底解决隐私问题”
- 不说“完全防止记忆泄露”
- 不说“差分隐私同步已生产可用”
- 不说“沙箱已经是真实 TEE 隔离”

更稳妥的表达：

> 本项目提出了一条面向手机智能体长期记忆的治理路线：先把记忆对象化，再把使用控制前置到检索链路中，随后通过降级输出和受控分析解决高敏记忆可用性问题，最后用脱敏同步支持跨设备连续体验。已有原型实验验证了关键机制的方向有效，后续可以围绕真实接线、真实沙箱和真实双设备同步继续补强。
