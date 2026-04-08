# OpenClaw 个性化记忆治理原型验证报告

更新日期：2026-04-08

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

此外，为了拆分不同策略层的贡献，后续又加入了一个轻量治理组：

- `guarded_light`

它只保留：

1. 域隔离
2. `pending_delete` 生命周期拒绝
3. 最轻量的用途控制

不做：

- `L2` 摘要优先
- `L3` sandbox 路由
- 高敏精细降级

### 3.3 核心指标

- `task_success_rate`
- `unauthorized_recall_rate`
- `sensitive_raw_exposure_rate`
- `cross_domain_leak_count`
- `policy_enforcement_rate`
- `audit_completeness_rate`
- `answer_quality_score`
- `summary_utility_score`
- `retrieval_latency_ms_p50/p95`
- `sandbox_overhead_ms_p50`
- `sync_overhead_ms_p50`
- `personalization_gain`
- `reidentification_risk_score`

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
| `real_chunk_guarded_light_v1` | 0.875 | 0.125 | 0.25 | 0 |
| `real_chunk_guarded_v1` | 0.875 | 0.125 | 0.25 | 0 |
| `real_chunk_guarded_v2` | 0.875 | 0.125 | 0.0 | 0 |

观察：

- chunk 化本身已经显著降低了暴露风险
- 加入轻量域隔离后，跨域串扰已经降到 0
- 但轻量治理下 `sensitive_raw_exposure_rate` 仍停在 `0.25`
- 对 `L2` 增加“摘要优先”后，高敏原文暴露率进一步降到 0
- 同时任务成功率维持在 `0.875`

补充指标：

- `real_chunk_baseline_v1`
  - `audit_completeness_rate = 1.0`
  - `answer_quality_score = 0.875`
  - `retrieval_latency_ms_p50 = 2.224`
- `real_chunk_guarded_light_v1`
  - `audit_completeness_rate = 1.0`
  - `answer_quality_score = 0.875`
  - `retrieval_latency_ms_p50 = 2.353`
- `real_chunk_guarded_v2`
  - `audit_completeness_rate = 1.0`
  - `answer_quality_score = 0.875`
  - `summary_utility_score = 0.25`
  - `retrieval_latency_ms_p50 = 2.409`

### 4.4 高敏记忆沙箱对照

| Mode | raw_exposure_rate | task_success_rate | summary_utility_score | sandbox_overhead_ms_p50 |
|---|---:|---:|---:|---:|
| `baseline_raw` | 1.0 | 1.0 | 1.0 | 0.0 |
| `summary_only` | 0.0 | 0.6667 | 0.6667 | 0.0 |
| `sandbox_job` | 0.0 | 1.0 | 1.0 | 2.518 |

观察：

- 直接返回原文时，可用性最高，但原文暴露不可接受
- 纯 `summary_only` 虽然保护了隐私，但任务成功率下降到 `0.6667`
- `sandbox_job` 在当前模拟中同时保住了 `task_success_rate = 1.0` 与 `raw_exposure_rate = 0.0`
- 代价是引入了可测得的受控分析开销，当前 `sandbox_overhead_ms_p50 = 2.518`

结论：

- 对高敏对象，简单摘要拒绝不是最佳点
- “受控分析式输出”更接近报告里提出的高敏记忆处理方向

### 4.5 跨设备同步降敏对照

| Mode | task_success_rate | personalization_gain | reidentification_risk_score | sync_overhead_ms_p50 |
|---|---:|---:|---:|---:|
| `local_only` | 0.0 | 0.0 | 0.0 | 0.002 |
| `raw_sync` | 1.0 | 1.0 | 0.95 | 0.003 |
| `summary_sync` | 1.0 | 1.0 | 0.0 | 0.002 |
| `dp_sync` | 0.6667 | 0.6667 | 0.0 | 0.01 |

观察：

- `raw_sync` 在当前模拟里能完整恢复个性化收益，但重识别风险很高
- `summary_sync` 保住了同等任务成功率，同时把风险压到 `0.0`
- `dp_sync` 进一步保留脱敏属性，但在当前近似实现下会损失一部分效用

结论：

- 报告里提出的“不同步原始记忆，而同步脱敏摘要/偏好表示”在原型层面是成立的
- 当前样例下，`summary_sync` 是比 `raw_sync` 更合理的默认折中

### 4.6 真实 OpenClaw 检索接线进展

当前仓库已经完成两层真实接线验证：

1. `fts-only` 原生 index/search 恢复
2. native candidate 上的 guarded wrapper 替代入口

关键结果：

- 五个 agent 的真实 native FTS 均已验证可用
- `native_search_success_rate = 1.0`
- `guard_native_cli_rate = 1.0`
- 已可通过 guarded wrapper 替代 `openclaw memory search`

结论：

- 真实接线已经从“实验模拟”推进到“本地可替换入口”
- 当前剩余差距是尚未改 OpenClaw 安装包内部实现

## 5. 关键结论

### 5.1 方案有效

根据真实 chunk、沙箱对照、同步对照和原生接线结果，可以认为报告中提出的总体方案在工程上是有效的，尤其是以下几点：

- 分级分类有效
- 策略前置有效
- 域隔离有效
- `L2` 摘要优先有效
- 高敏受控分析有效
- 脱敏同步有效

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

### 5.5 轻量策略和完整策略各自解决不同问题

风险对照实验表明：

- 轻量策略已经足够解决跨域串扰
- 但轻量策略不能解决 `L2` 原文暴露
- 完整策略的增量价值主要来自摘要优先与高敏受控输出

这意味着：

- “域隔离”可以先落地
- “摘要优先 / sandbox”是第二阶段必须补的增强层，而不是可有可无的细节

### 5.6 同步默认应优先采用 summary-first，而不是 raw-sync

跨设备同步对照说明：

- `raw_sync` 的收益高，但风险也高
- `summary_sync` 在当前样例里保住了同等收益，同时显著降低风险
- `dp_sync` 代表进一步保护的方向，但当前近似实现下要接受效用下降

因此，当前原型最合理的同步默认策略是：

- 先用 `summary_sync`
- 再逐步演进到更严格的 DP/聚合方案

## 6. 局限

当前原型仍有明显边界：

- 尚未直接改 OpenClaw 内部检索链路实现
- 尚未接入真实 OPA / OpenFGA
- 尚未接入真实 gVisor / Firecracker
- 差分隐私同步仍是摘要级近似模拟
- 摘要降级目前还是启发式实现，不是成熟摘要模型

因此，本报告给出的结论是：

- 方案已被原型初步验证有效
- 但仍属于“外挂式治理层 + 启发式策略”的验证结果

## 6.1 验证边界与有效性说明

为了避免把“原型有效”误写成“系统已完备”，这里对当前仓库能验证什么、不能验证什么做一版收口。

### 已被初步验证的部分

1. **分级分类到策略联动是可行的**  
   当前仓库已经把分类结果真正用于检索前的 `allow / deny / downgrade / sandbox` 决策，而不是停留在标签展示层。

2. **chunk 化与 `raw_text / retrieval_text` 分层是必要条件**  
   真实整文件实验和真实 chunk 实验已经共同说明，若直接把整份 session 文件当治理对象，治理粒度过粗，既损害可用性，也抬高敏感度。

3. **策略前置与域隔离有效**  
   真实 chunk 场景下，`cross_domain_leak_count` 已经从 `4` 降到 `0`，说明个人域、工作域和第三方域的逻辑边界是可以在 OpenClaw 基线上被治理层稳定利用的。

4. **`L2` 摘要优先有效**  
   风险对照实验显示，轻量策略已经足以消除跨域串扰，但只有完整策略才能把 `sensitive_raw_exposure_rate` 从 `0.25` 压到 `0.0`。

5. **高敏记忆更适合受控分析，而不是简单拒绝**  
   沙箱对照实验表明，`summary_only` 会损失可用性，而 `sandbox_job` 在当前模拟中可以同时保住 `task_success_rate = 1.0` 与 `raw_exposure_rate = 0.0`。

6. **跨设备同步默认更适合 `summary_sync`，而不是 `raw_sync`**  
   同步实验表明，`raw_sync` 虽能保留收益，但重识别风险过高；`summary_sync` 在当前样例里保留了同等任务成功率，同时把风险压到 `0.0`。

7. **治理层可以挂到真实 OpenClaw 检索链路旁边工作**  
   native FTS 恢复、guard adapter 和 guarded wrapper 已说明，这套原型不仅能在离线实验集上跑，也能消费真实 `openclaw memory search --json` 候选。

### 尚未被完整验证的部分

1. **真实隔离沙箱尚未验证**  
   当前 `sandbox_job` 仍是模拟受控分析器，不是真实 gVisor、Firecracker、TEE 或等价隔离执行环境。

2. **真实双设备同步尚未验证**  
   当前同步实验使用的是模拟双设备数据集，不是真实设备间的同步链路。

3. **严格差分隐私与安全聚合尚未验证**  
   当前 `dp_sync` 是摘要级近似模拟，不是正式 DP 训练、隐私预算管理或安全聚合实现。

4. **OpenClaw 内核级集成尚未验证**  
   当前已经有可替代 `openclaw memory search` 的 wrapper/shim，但尚未直接修改 OpenClaw 安装包内部检索返回逻辑。

5. **外置策略引擎尚未验证**  
   当前策略仍以内嵌规则为主，没有正式接入 OPA / OpenFGA。

6. **分级加密与密钥层次设计尚未验证**  
   第 4.2 节提出的分层加密、场景密钥和会话密钥设计，目前还停留在方案层，没有形成真实实现对照实验。

### 本报告可支撑的结论边界

因此，当前仓库可以支撑这样一个谨慎但明确的结论：

- `content.md` 提出的核心框架在原型层面是有效的；
- 其中证据最强的是 `chunk 化`、`分层表示`、`策略前置`、`域隔离`、`L2` 摘要优先、`高敏受控输出` 和 `脱敏同步方向`；
- 但关于真实隔离沙箱、严格 DP/安全聚合、外置策略引擎、分级加密体系和 OpenClaw 内核级集成，目前还不能宣称“已完成验证”。

## 7. 建议

### 7.1 面向工程继续推进

建议优先继续做：

1. 将 `memory-guard` 接到真实 OpenClaw 检索前
2. 将 `memory-classify` 的产物持久化为稳定治理表
3. 将 `L2` 摘要输出替换为更稳健的摘要器
4. 将高敏共享改为真实 sandbox job
5. 将模拟同步评测迁移到更真实的双设备数据流

### 7.2 面向系统能力沉淀

本仓库已经将有效机制沉淀为四个 skill 原型：

- [`memory-classify`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-classify/SKILL.md)
- [`memory-guard`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-guard/SKILL.md)
- [`memory-audit`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-audit/SKILL.md)
- [`memory-sandbox-share`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-sandbox-share/SKILL.md)

这意味着：

- 报告中的框架已经不仅是论证对象，也已经具备了向可复用能力模块演化的基础
