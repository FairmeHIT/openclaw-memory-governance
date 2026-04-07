# OpenClaw 个性化记忆治理原型验证报告

更新日期：2026-04-07

## 1. 研究目标

本原型验证围绕 [`content.md`](/Users/fairme/Codes/openclaw-personalized-memory/content.md) 中提出的方案展开，目标不是重做一个记忆系统，而是验证以下机制在 OpenClaw 本地基线上是否有效：

- 记忆分级分类
- 检索前策略控制
- 个人域 / 工作域 / 第三方域隔离
- 高敏记忆受控使用
- 原始表示与检索表示分层
- 审计留痕与指标评估

验证口径聚焦三个问题：

1. 是否能减少越权召回和跨域串扰
2. 是否能降低高敏原文暴露
3. 是否在安全性提升的同时保持基本可用性

## 2. 实验对象

实验对象分为三类：

### 2.1 半合成样例数据

来源：

- [`memory_samples.jsonl`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/datasets/memory_samples.jsonl)
- [`query_set.jsonl`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/datasets/query_set.jsonl)

用途：

- 快速验证治理框架的正确性
- 观察基线与治理后的方向性差异

### 2.2 真实 OpenClaw 整文件数据

来源：

- 从 `~/.openclaw/workspace-*/memory/*.md` 导出
- 对应脚本：
  [`export_openclaw_memories.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/export_openclaw_memories.py)
  [`classify_real_memories.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/classify_real_memories.py)

用途：

- 观察 OpenClaw 原始 session 文件在真实形态下的治理难点

### 2.3 真实 OpenClaw chunk 数据

来源：

- 将真实 session 文件进一步切成片段级 chunk
- 对应脚本：
  [`chunk_real_memories.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/chunk_real_memories.py)

用途：

- 验证“chunk 化 + 分层表示 + 策略前置”是否比整文件治理更有效

## 3. 方法

### 3.1 基线组

基线组只做简单检索，不做治理控制：

- 不做域隔离
- 不做隐私等级判断
- 不做摘要降级
- 不做受控共享

对应脚本：

- [`run_baseline.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/run_baseline.py)

### 3.2 治理组

治理组增加以下机制：

1. 对记忆对象打治理标签
2. 检索前进行 allow / deny / downgrade / sandbox 判定
3. 跨域默认拒绝
4. `L3` 默认沙箱或拒绝
5. `L2` 默认摘要优先，不直接返回原文
6. 写入审计日志并计算指标

对应脚本：

- [`run_guarded.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/run_guarded.py)
- [`compute_metrics.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/compute_metrics.py)

### 3.3 核心指标

- `task_success_rate`
- `unauthorized_recall_rate`
- `sensitive_raw_exposure_rate`
- `cross_domain_leak_count`
- `policy_enforcement_rate`

## 4. 实验结果

### 4.1 半合成样例数据

| Run | task_success_rate | unauthorized_recall_rate | sensitive_raw_exposure_rate | cross_domain_leak_count |
|---|---:|---:|---:|---:|
| `baseline_v1` | 1.0 | 1.4 | 1.0 | 6 |
| `guarded_v1` | 0.7 | 0.2 | 0.2 | 1 |

观察：

- 治理层显著降低了越权召回和高敏原文暴露
- 同时带来一定可用性损失
- 该阶段说明总体方向成立，但还不够细

### 4.2 真实整文件数据

| Run | task_success_rate | unauthorized_recall_rate | sensitive_raw_exposure_rate | cross_domain_leak_count |
|---|---:|---:|---:|---:|
| `real_baseline_v1` | 1.0 | 1.5 | 1.0 | 6 |
| `real_guarded_v1` | 0.875 | 0.625 | 0.875 | 0 |

观察：

- 域隔离在真实数据中有效，跨域串扰降到 0
- 但高敏原文暴露仍然很高
- 原因是整份 session 文件中混有大量 message/session metadata，导致治理对象过粗

结论：

- 仅靠“整文件 + 域策略”不够
- 必须进一步切块

### 4.3 真实 chunk 数据

| Run | task_success_rate | unauthorized_recall_rate | sensitive_raw_exposure_rate | cross_domain_leak_count |
|---|---:|---:|---:|---:|
| `real_chunk_baseline_v1` | 1.0 | 0.75 | 0.25 | 4 |
| `real_chunk_guarded_v1` | 0.875 | 0.125 | 0.25 | 0 |
| `real_chunk_guarded_v2` | 0.875 | 0.125 | 0.0 | 0 |

观察：

- chunk 化本身已经显著降低了暴露风险
- 加入域隔离后，跨域串扰降到 0
- 对 `L2` 增加“摘要优先”后，高敏原文暴露率进一步降到 0
- 同时任务成功率维持在 `0.875`

## 5. 关键结论

### 5.1 方案有效

根据真实 chunk 结果，可以认为报告中提出的总体方案在工程上是有效的，尤其是以下四点：

- 分级分类有效
- 策略前置有效
- 域隔离有效
- `L2` 摘要优先有效

### 5.2 治理粒度决定成败

实验最重要的发现不是某条规则本身，而是：

- 治理对象必须是 chunk，而不是整文件

如果直接把 OpenClaw 的 session `.md` 文件当成检索和策略对象：

- 过度敏感
- 误杀较多
- 可用性和安全性都不理想

### 5.3 `raw_text` / `retrieval_text` 必须分层

实验表明：

- 原始 session 文件包含大量显式标识符和上下文元数据
- 若不区分原始表示与检索表示，绝大多数内容都只能按高敏处理

因此，报告中的“分层表示”不是附加优化，而是必要条件。

### 5.4 域隔离优先级高于复杂授权

在当前原型阶段，只用相对简单的域映射和检索前规则，就已经把真实串扰降到 0。

这说明：

- 在 OpenClaw 这类本地多 workspace 结构里，先把域边界立住，收益很高

## 6. 局限

当前原型仍有明显边界：

- 尚未直接接入 OpenClaw 内部检索链路
- 尚未接入真实 OPA / OpenFGA
- 尚未接入真实 gVisor / Firecracker
- 差分隐私同步仍停留在方案阶段
- 摘要降级目前还是启发式实现，不是成熟摘要模型

因此，本报告给出的结论是：

- 方案已被原型初步验证有效
- 但仍属于“外挂式治理层 + 启发式策略”的验证结果

## 7. 建议

### 7.1 面向工程继续推进

建议优先继续做：

1. 将 `memory-guard` 接到真实 OpenClaw 检索前
2. 将 `memory-classify` 的产物持久化为稳定治理表
3. 将 `L2` 摘要输出替换为更稳健的摘要器
4. 将高敏共享改为真实 sandbox job

### 7.2 面向系统能力沉淀

本仓库已经将有效机制沉淀为四个 skill 原型：

- [`memory-classify`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-classify/SKILL.md)
- [`memory-guard`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-guard/SKILL.md)
- [`memory-audit`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-audit/SKILL.md)
- [`memory-sandbox-share`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-sandbox-share/SKILL.md)

这意味着：

- 报告中的框架已经不仅是论证对象，也已经具备了向可复用能力模块演化的基础
