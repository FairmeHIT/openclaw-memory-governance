# Architecture

本文档说明本仓库原型的架构边界、数据流和模块职责。

## 1. 总体目标

原型的目标不是替换 OpenClaw 的记忆系统，而是在它的本地基线之上增加一层“记忆治理层”。

该治理层负责：

- 把原始记忆变成可治理对象
- 在检索前做策略判定
- 对敏感内容进行降级或受控处理
- 记录审计与实验指标

## 2. 架构分层

从下到上可以分为五层。

### 2.1 OpenClaw 基线层

输入来源：

- `~/.openclaw/workspace-*/memory/*.md`
- `~/.openclaw/logs/*`
- `~/.openclaw/memory/main.sqlite`

作用：

- 提供原始记忆文件
- 提供多 workspace / 多 agent 运行结构
- 提供 OpenClaw 原生工作区边界

说明：

- 当前实验主要读取 `workspace-*/memory/*.md`
- 由于当前本地 `main.sqlite` 中没有有效 chunk，因此实验以文件导出和自建 chunk 为主

### 2.2 表示转换层

职责：

- 从原始 `.md` 文件提取可实验对象
- 将整文件转换为 file-level 或 chunk-level 记录
- 分离 `raw_text` 与 `retrieval_text`

对应脚本：

- [`export_openclaw_memories.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/export_openclaw_memories.py)
- [`chunk_real_memories.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/chunk_real_memories.py)
- [`classify_openclaw_memory.py`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-classify/scripts/classify_openclaw_memory.py)

关键点：

- `raw_text` 保留原始内容
- `retrieval_text` 去除显式 ID 和多余元数据，只保留检索所需语义

### 2.3 治理元数据层

职责：

- 给每个记忆对象补充治理属性
- 独立保存治理信息，不直接改写原始记忆文件

核心字段：

- `privacy_level`
- `domain`
- `purpose_allow`
- `lifecycle`
- `sync_policy`
- `index_policy`

对应 schema：

- [`memory_governance.sql`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/schemas/memory_governance.sql)

对应脚本：

- [`seed_dataset.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/seed_dataset.py)

### 2.4 策略执行层

职责：

- 在候选命中与返回之间做策略判定
- 输出 `allow / deny / downgrade / sandbox`

对应脚本：

- [`run_guarded.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/run_guarded.py)
- [`guard_memory_retrieval.py`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-guard/scripts/guard_memory_retrieval.py)

当前默认策略：

- 跨域默认拒绝
- `shared` 可跨域
- `L3` 默认 `sandbox` 或拒绝
- `L2` 默认 `downgrade`
- `external_share` 对 `L2/L3` 不返回原文

### 2.5 审计与评估层

职责：

- 记录所有决策过程
- 计算实验指标
- 支撑后续汇报和对照分析

对应脚本：

- [`compute_metrics.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/compute_metrics.py)
- [`compute_memory_metrics.py`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-audit/scripts/compute_memory_metrics.py)

### 2.6 受控共享层

职责：

- 对高敏 chunk 做 summary-only 输出
- 模拟沙箱共享

对应脚本：

- [`sandbox_share.py`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-sandbox-share/scripts/sandbox_share.py)

## 3. 数据流

### 3.1 从 OpenClaw 到治理对象

```text
OpenClaw memory markdown
  -> 导出
  -> 清洗/切块
  -> raw_text / retrieval_text
  -> governance labels
  -> governed dataset
```

### 3.2 从查询到结果

```text
query
  -> baseline retrieval or candidate retrieval
  -> policy check
  -> allow / deny / downgrade / sandbox
  -> returned chunks or summary-only output
  -> audit logs
  -> metrics
```

### 3.3 从高敏请求到受控共享

```text
sensitive request
  -> candidate L2/L3 chunks
  -> block raw output
  -> summary_only or sandbox job
  -> audit record
```

## 4. 文件级与 chunk 级两条路径

本仓库存在两条实验路径。

### 4.1 文件级路径

特点：

- 粒度粗
- 便于快速验证策略方向
- 容易把正常内容和高敏元数据混在一起

优点：

- 实现简单
- 易于观察 OpenClaw 原始 session 文件的真实问题

缺点：

- 敏感度偏高
- 可用性和准确性不够理想

### 4.2 chunk 级路径

特点：

- 粒度细
- 可区分普通对话内容、角色描述、模型信息和显式敏感片段

优点：

- 更贴近报告中的“记忆对象化治理”
- 能显著降低误杀和过度高敏化
- 能支持 `L2` 摘要优先策略

结论：

- 当前仓库把 chunk 级路径视为主要有效路径

## 5. 模块职责图

```text
OpenClaw Workspace Memory
  -> memory-classify
     -> governed dataset
        -> memory-guard
           -> allow / deny / downgrade / sandbox
              -> memory-audit
              -> memory-sandbox-share
```

职责拆分如下：

- `memory-classify`
  解决“记忆是什么、应如何打标”
- `memory-guard`
  解决“哪些记忆能返回、以什么形式返回”
- `memory-audit`
  解决“如何证明策略有效”
- `memory-sandbox-share`
  解决“高敏内容如何有限使用而不直接外泄”

## 6. 为什么要区分 `raw_text` 和 `retrieval_text`

这是整个原型中最重要的架构决定之一。

### `raw_text`

特点：

- 保留原始信息
- 可能包含显式 ID、message metadata、session metadata
- 适合审计和原始留存

### `retrieval_text`

特点：

- 去掉或归一化显式标识符
- 保留检索所需语义
- 适合参与召回、摘要和策略判断

如果不区分两者：

- 几乎所有真实 session 文件都会被判为高敏
- 既影响检索效果，也影响治理粒度

## 7. 当前实现边界

当前架构仍然是“外挂式治理层”，不直接改 OpenClaw 核心。

意味着：

- 它适合验证方案有效性
- 也适合作为 skills 原型
- 但还没有变成 OpenClaw 内部正式子系统

当前未接入：

- OpenClaw 内部原生检索 hook
- OpenFGA / OPA
- gVisor / Firecracker
- 差分隐私同步流水线

## 8. 建议的下一步架构演进

### 8.1 与 OpenClaw 更深集成

- 将 `memory-classify` 接到记忆写入后
- 将 `memory-guard` 接到检索返回前
- 将治理元数据与 chunk 索引绑定

### 8.2 外置策略引擎

- 用 OpenFGA 管 access relation
- 用 OPA 管 usage control

### 8.3 真实沙箱执行

- 将 `memory-sandbox-share` 从逻辑模拟升级为真实 sandbox runner

### 8.4 同步治理

- 在 `raw_text` 不出端的前提下，只同步标签、摘要或 DP 更新
