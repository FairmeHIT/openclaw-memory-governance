# OpenClaw 基线上的个性化记忆治理原型验证方案

更新日期：2026-04-07

## 1. 目标

本方案的目标不是重新实现一个记忆系统，而是在你已安装的 OpenClaw 基线之上，验证 [`content.md`](/Users/fairme/Codes/openclaw-personalized-memory/content.md) 中提出的框架是否有效。

要验证的核心命题有四个：

1. 记忆分级分类是否能真正驱动检索和共享行为
2. 个人域 / 工作域 / 第三方域隔离是否能减少跨场景串扰
3. 高敏记忆是否能避免普通召回，并只在受控环境中被有限使用
4. 在增加治理机制后，系统是否仍保持可用，且性能代价可接受

最终要产出的不是概念说明，而是可复现实验结论，包括：

- 日志证据
- 指标对比
- 实验报告
- 可沉淀为 OpenClaw skills 的能力模块

## 2. 现有基线与切入点

你本地 `~/.openclaw` 已经具备原型验证所需的关键对象：

- 明文记忆文件：`~/.openclaw/workspace-*/memory/`
- 记忆索引：`~/.openclaw/memory/main.sqlite`
- 配置与行为日志：`~/.openclaw/logs/`
- 多 agent / 多 workspace 结构：`workspace-main`、`workspace-code`、`workspace-content`、`workspace-assistant`、`workspace-zhixi`

这意味着原型可以先采用“外挂式治理层”，而不是直接修改 OpenClaw 核心：

1. 读取 OpenClaw 已写入的记忆文件和 chunk 索引
2. 为每个 chunk 补充治理元数据
3. 在检索前做策略判定
4. 对结果做允许、拒绝、降级或转沙箱
5. 记录审计日志并汇总实验指标

## 3. 原型验证的总体策略

采用“三阶段、两类对照、四类证据”的方式推进。

### 3.1 三阶段

#### 阶段 A：分类驱动检索

验证：

- L0-L3 隐私等级是否真的影响召回
- domain 是否真的影响访问边界
- lifecycle / purpose 是否真的影响读取许可

输出：

- chunk 分类结果
- 检索前策略判定日志
- 基线 vs 治理后指标对比

#### 阶段 B：高敏记忆受控使用

验证：

- L3 记忆是否能退出普通召回路径
- 外部请求是否只能获得摘要/统计而不是原文
- 审计链是否完整

输出：

- 沙箱任务日志
- 原文暴露检查结果
- 任务完成率对比

#### 阶段 C：跨设备同步降敏验证

验证：

- 是否可以只同步脱敏摘要、标签、模型更新，而不直接同步原始记忆
- 是否在牺牲有限精度的情况下显著降低隐私风险

输出：

- 同步前后个性化表现对比
- 隐私预算或噪声强度记录
- 重识别风险评估

### 3.2 两类对照

#### 对照一：功能对照

- 基线组：原生 OpenClaw 记忆检索
- 实验组：OpenClaw + 治理层

#### 对照二：风险对照

- 宽松策略组：只按关键词或简单域限制
- 完整策略组：分级分类 + 用途控制 + 生命周期 + 受控共享

### 3.3 四类证据

- 结构化日志
- 自动计算指标
- 关键案例回放
- 最终实验结论

## 4. 原型架构

推荐在仓库中增加一个独立实验目录，例如：

```text
experiments/
  datasets/
  runs/
  scripts/
  reports/
prototype/
  classifier/
  policy/
  retrieval_guard/
  audit/
  sandbox/
```

### 4.1 核心模块

#### 1. `memory-classifier`

职责：

- 读取 `workspace-*/memory/*.md`
- 对应到 `main.sqlite` 中的 chunk
- 为每个 chunk 打治理标签

最小元数据建议：

- `chunk_id`
- `file_path`
- `agent_id`
- `domain`
- `privacy_level`
- `source_trust`
- `purpose_allow`
- `lifecycle`
- `sync_policy`
- `index_policy`

#### 2. `policy-engine`

职责：

- 根据查询上下文决定是否允许访问 chunk
- 输出 allow / deny / downgrade / sandbox

输入建议：

- 主体：`agent_id`、`workspace`、`role`
- 客体：`chunk_id`、`privacy_level`、`domain`、`lifecycle`
- 环境：`purpose`、`sandbox`、`export_mode`

#### 3. `retrieval-guard`

职责：

- 拦截检索请求
- 对候选 chunk 执行策略裁剪
- 生成最终可用结果集

输出建议：

- 原始候选集
- 允许集
- 拒绝集
- 降级集
- 触发沙箱集

#### 4. `audit-recorder`

职责：

- 记录所有检索、拒绝、导出、同步、沙箱执行事件
- 支撑后续指标统计和案例回放

#### 5. `sandbox-runner`

职责：

- 承接 L3 或跨域高风险分析请求
- 只输出摘要、标签、统计结果
- 不直接返回原始 chunk 文本

第一版可先用逻辑沙箱模拟，第二版再接 gVisor。

## 5. 数据对象与治理元数据设计

建议在实验阶段先单独建立一张治理表，而不是直接改 OpenClaw 的原生 memory schema。

例如：

```sql
CREATE TABLE memory_governance (
  chunk_id TEXT PRIMARY KEY,
  file_path TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  domain TEXT NOT NULL,
  privacy_level TEXT NOT NULL,
  source_trust TEXT NOT NULL,
  purpose_allow TEXT NOT NULL,
  lifecycle TEXT NOT NULL,
  sync_policy TEXT NOT NULL,
  index_policy TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

建议初始取值：

- `domain`: `personal` / `work` / `third_party` / `shared`
- `privacy_level`: `L0` / `L1` / `L2` / `L3`
- `source_trust`: `explicit_user` / `agent_inferred` / `external_import`
- `purpose_allow`: `personalization` / `task_continuity` / `summary_only` / `sandbox_only` / `deny_external`
- `lifecycle`: `short` / `mid` / `long` / `pending_delete`
- `sync_policy`: `local_only` / `summary_only` / `dp_sync`
- `index_policy`: `full_index` / `restricted_index` / `no_vector_recall`

## 6. 实验数据集设计

不能只用真实记忆做实验，否则难以量化。建议构造一套半合成数据集。

### 6.1 数据集构成

建议 80 到 120 条记忆，覆盖：

- 个人偏好
- 私人关系
- 日程习惯
- 工作任务
- 工作机密
- 财务信息
- 健康信息
- 跨域混合信息
- 外部导入信息
- 误导性或污染性内容

### 6.2 标注维度

每条记忆都应人工标注：

- 正确 domain
- 正确 privacy_level
- 是否应进入向量索引
- 哪些 purpose 可以访问
- 是否允许同步

### 6.3 查询集

建议构造 40 到 60 个测试查询，分成：

- 合法个人域检索
- 合法工作域检索
- 跨域诱导查询
- 高敏探测查询
- 第三方摘要请求
- 同步/共享场景请求

## 7. 实验矩阵

### 实验 1：分类质量验证

目的：

- 验证分类器本身是否足够可用

输入：

- 已人工标注的数据集

输出指标：

- `privacy_level_accuracy`
- `domain_accuracy`
- `index_policy_accuracy`

结论标准：

- 若分类准确率过低，后续治理实验结论不可靠

### 实验 2：基线检索对照

目的：

- 验证治理层是否减少越权召回

分组：

- A 组：原生 OpenClaw
- B 组：OpenClaw + retrieval guard

输出指标：

- `task_success_rate`
- `unauthorized_recall_rate`
- `sensitive_raw_exposure_rate`
- `retrieval_latency_ms`

期望：

- `unauthorized_recall_rate` 明显下降
- `sensitive_raw_exposure_rate` 接近 0
- `task_success_rate` 保持在可接受范围

### 实验 3：跨域串扰验证

目的：

- 验证 personal/work/third_party 域隔离是否有效

方法：

- 将不同域记忆分布在不同 workspace 或逻辑 domain
- 构造跨域诱导查询

输出指标：

- `cross_domain_leak_count`
- `blocked_cross_domain_requests`
- `downgraded_cross_domain_responses`

### 实验 4：高敏记忆沙箱验证

目的：

- 验证 L3 记忆是否仅在受控模式下使用

分组：

- 普通检索
- 沙箱摘要

输出指标：

- `l3_plaintext_exposure_count`
- `sandbox_job_success_rate`
- `summary_utility_score`
- `audit_completeness_rate`

### 实验 5：同步降敏验证

目的：

- 验证只同步降敏信息时是否仍有个性化收益

分组：

- 原始摘要同步
- DP/脱敏同步

输出指标：

- `personalization_gain`
- `reidentification_risk_score`
- `sync_payload_size`
- `privacy_budget_epsilon`

## 8. 指标定义

建议在第一版就把指标写死，避免实验后口径漂移。

### 8.1 安全与治理指标

- `unauthorized_recall_rate`
  - 未获授权 chunk 被最终返回的比例
- `sensitive_raw_exposure_rate`
  - L2/L3 原文被直接暴露的比例
- `cross_domain_leak_count`
  - personal/work/third_party 串扰次数
- `policy_enforcement_rate`
  - 应拦截请求中被正确拦截的比例
- `audit_completeness_rate`
  - 关键事件是否全部有日志记录

### 8.2 可用性指标

- `task_success_rate`
  - 合法任务成功完成的比例
- `answer_quality_score`
  - 用人工或模型评估答案是否仍可用
- `summary_utility_score`
  - 只给摘要而不给原文时的任务可完成度

### 8.3 性能指标

- `retrieval_latency_ms`
- `policy_eval_latency_ms`
- `sandbox_overhead_ms`
- `sync_overhead_ms`

### 8.4 分类指标

- `privacy_level_accuracy`
- `domain_accuracy`
- `purpose_allow_accuracy`

## 9. 日志 schema

建议所有实验统一写 JSONL，便于统计与追踪。

### 9.1 检索判定日志 `policy_decisions.jsonl`

```json
{
  "ts": "2026-04-07T12:00:00Z",
  "query_id": "q_001",
  "agent_id": "main",
  "workspace": "workspace-main",
  "purpose": "task_continuity",
  "candidate_chunk_ids": ["c1", "c2", "c3"],
  "allowed_chunk_ids": ["c1"],
  "denied_chunk_ids": ["c2"],
  "downgraded_chunk_ids": ["c3"],
  "sandbox_chunk_ids": [],
  "deny_reasons": {
    "c2": "cross_domain",
    "c3": "summary_only"
  },
  "policy_eval_latency_ms": 18
}
```

### 9.2 暴露日志 `exposures.jsonl`

```json
{
  "ts": "2026-04-07T12:00:01Z",
  "query_id": "q_001",
  "returned_chunk_ids": ["c1"],
  "raw_exposure": false,
  "exposed_privacy_levels": ["L1"]
}
```

### 9.3 审计日志 `audit_events.jsonl`

```json
{
  "ts": "2026-04-07T12:00:01Z",
  "event_type": "retrieval_allow",
  "agent_id": "main",
  "chunk_id": "c1",
  "domain": "work",
  "privacy_level": "L1",
  "purpose": "task_continuity",
  "decision": "allow"
}
```

### 9.4 沙箱作业日志 `sandbox_jobs.jsonl`

```json
{
  "ts": "2026-04-07T12:03:00Z",
  "job_id": "sbx_001",
  "request_id": "q_014",
  "agent_id": "third_party_proxy",
  "input_privacy_levels": ["L3"],
  "output_mode": "summary_only",
  "raw_output_blocked": true,
  "status": "success",
  "latency_ms": 240
}
```

## 10. 试验结论的判定标准

报告最终不能只说“看起来有效”，需要明确判定口径。

建议结论按三档：

### 10.1 有效

满足：

- 越权召回率显著下降
- 高敏原文暴露率接近 0
- 跨域串扰显著减少
- 合法任务成功率下降有限
- 性能开销在可接受范围

### 10.2 部分有效

满足：

- 安全性提升明显
- 但分类误差、策略过严或性能问题影响可用性

### 10.3 无效或不稳定

满足：

- 分类精度不足以支撑策略
- 越权召回和原文暴露仍频繁出现
- 正常任务成功率下降过大

## 11. 实施顺序

建议按下面顺序做，避免一开始就把范围做炸：

1. 建立实验数据集与查询集
2. 建 memory governance 元数据表
3. 实现分类器和人工校正流程
4. 实现 retrieval guard 与审计记录
5. 跑基线对照实验
6. 实现 L3 沙箱处理
7. 跑高敏受控实验
8. 最后再做同步降敏实验

## 12. 后续沉淀为 OpenClaw skills 的拆分建议

如果实验结论成立，不建议做成一个“大一统 skill”，而建议拆成可组合能力。

### `memory-classify`

能力：

- 扫描新记忆
- 标注 `L0-L3`、domain、purpose、lifecycle

### `memory-guard`

能力：

- 检索前执行策略判定
- 阻断越权召回
- 对高敏结果做降级

### `memory-audit`

能力：

- 记录检索、拒绝、导出、沙箱与同步事件
- 生成实验和运行期审计报告

### `memory-sandbox-share`

能力：

- 对高敏记忆只允许摘要/统计型共享
- 不暴露原始文本

### `memory-sync-dp`

能力：

- 输出只适合同步的脱敏摘要、标签或 DP 更新

## 13. 当前最务实的 MVP 边界

第一版 MVP 只做下面这些就够了：

- 一套人工标注的小型记忆数据集
- 一张治理元数据表
- 一个基于规则的分类器
- 一个检索前拦截器
- 一套 JSONL 审计日志
- 一组基线 vs 治理后指标对照

只要这一版能证明：

- 越权召回下降
- L3 原文不再被普通召回
- 合法任务仍基本可完成

就足够说明报告中的总体方案具有工程可验证性，后续再继续增强成 skills 是合理的。
