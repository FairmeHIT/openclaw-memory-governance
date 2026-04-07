# OpenClaw Personalized Memory

基于 OpenClaw 本地基线的个性化记忆治理原型验证仓库。

本仓库围绕 [`content.md`](./content.md) 中提出的方案，验证以下技术路线是否有效：

- 记忆分级分类
- 检索前策略判定
- 个人域 / 工作域 / 第三方域隔离
- 高敏记忆受控使用
- `raw_text` / `retrieval_text` 分层表示
- 审计留痕与指标验证

## 仓库内容

- [`content.md`](./content.md)
  研究报告原文
- [`github-analysis.md`](./github-analysis.md)
  相关 GitHub 项目调研与原型选型结论
- [`prototype-validation-plan.md`](./prototype-validation-plan.md)
  原型验证方案
- [`experiments/`](./experiments/README.md)
  数据集、schema、实验脚本、运行结果
- [`skills/`](./skills)
  沉淀出的 memory governance skills 原型
- [`Makefile`](./Makefile)
  一键运行实验与 skills demo 的常用命令
- [`experiments/releases/v1/`](./experiments/releases/v1/README.md)
  第一轮发布版实验结果快照

## 快速开始

先查看可用命令：

```bash
make help
```

常用入口：

```bash
make export-real
make chunk-real
make real-chunk-db
make real-chunk-baseline
make real-chunk-guarded
make real-chunk-metrics
```

skills demo：

```bash
make skill-classify-demo
make skill-guard-demo
make skill-audit-demo
make skill-sandbox-demo
```

## 设计结论

本仓库最终验证的不是“再做一个 memory store”，而是验证一套治理闭环：

1. 从 OpenClaw `workspace-*/memory/*.md` 提取记忆
2. 将原始 session 文件切成更细的 chunk
3. 为每个 chunk 标注 `privacy_level / domain / purpose / lifecycle / sync_policy / index_policy`
4. 在检索前执行 allow / deny / downgrade / sandbox 决策
5. 对高敏内容默认摘要化，而不是直接返回原文
6. 对所有决策写审计日志并计算指标

## 关键发现

### 1. 整文件治理不够好

真实 OpenClaw session 文件中混有大量 `message_id`、`sender_id`、session metadata。

如果直接把整份 `.md` 文件当作治理对象：

- 几乎所有记忆都会被判为高敏
- 检索和治理粒度过粗
- 正常可用性和隐私性都会被拖累

### 2. 片段级治理有效

将真实记忆切成 chunk 后，真实数据分布从“几乎全是高敏”变成：

- `L0 = 68`
- `L1 = 60`
- `L2 = 17`

这说明：

- 治理对象必须是 chunk，而不是整文件
- `raw_text` 与 `retrieval_text` 必须分层

### 3. 域隔离是有效的

在真实 chunk 场景中，加上检索前策略后：

- `cross_domain_leak_count` 从 `4` 降到 `0`

### 4. L2 默认摘要降级有效

在真实 chunk 场景中，将 `L2` 默认策略从“直接允许原文返回”改为“命中但降级为摘要”后：

- `sensitive_raw_exposure_rate` 从 `0.25` 降到 `0.0`
- `task_success_rate` 仍保持 `0.875`

这说明：

- `summary-first` 是比简单拒绝更合理的 `L2` 策略

## 关键实验结果

### 半合成样例数据

| Run | task_success_rate | unauthorized_recall_rate | sensitive_raw_exposure_rate | cross_domain_leak_count |
|---|---:|---:|---:|---:|
| `baseline_v1` | 1.0 | 1.4 | 1.0 | 6 |
| `guarded_v1` | 0.7 | 0.2 | 0.2 | 1 |

来源：

- [`baseline_v1/metrics.json`](./experiments/runs/baseline_v1/metrics.json)
- [`guarded_v1/metrics.json`](./experiments/runs/guarded_v1/metrics.json)

### 真实 OpenClaw 整文件数据

| Run | task_success_rate | unauthorized_recall_rate | sensitive_raw_exposure_rate | cross_domain_leak_count |
|---|---:|---:|---:|---:|
| `real_baseline_v1` | 1.0 | 1.5 | 1.0 | 6 |
| `real_guarded_v1` | 0.875 | 0.625 | 0.875 | 0 |

来源：

- [`real_baseline_v1/metrics.json`](./experiments/runs/real_baseline_v1/metrics.json)
- [`real_guarded_v1/metrics.json`](./experiments/runs/real_guarded_v1/metrics.json)

### 真实 OpenClaw chunk 数据

| Run | task_success_rate | unauthorized_recall_rate | sensitive_raw_exposure_rate | cross_domain_leak_count |
|---|---:|---:|---:|---:|
| `real_chunk_baseline_v1` | 1.0 | 0.75 | 0.25 | 4 |
| `real_chunk_guarded_v1` | 0.875 | 0.125 | 0.25 | 0 |
| `real_chunk_guarded_v2` | 0.875 | 0.125 | 0.0 | 0 |

来源：

- [`real_chunk_baseline_v1/metrics.json`](./experiments/runs/real_chunk_baseline_v1/metrics.json)
- [`real_chunk_guarded_v1/metrics.json`](./experiments/runs/real_chunk_guarded_v1/metrics.json)
- [`real_chunk_guarded_v2/metrics.json`](./experiments/runs/real_chunk_guarded_v2/metrics.json)

## 仓库结构

```text
.
├── content.md
├── github-analysis.md
├── prototype-validation-plan.md
├── experiments/
│   ├── datasets/
│   ├── schemas/
│   ├── scripts/
│   ├── runs/
│   └── reports/
├── prototype/
└── skills/
```

### `experiments/`

- `datasets/`
  半合成数据、真实导出数据、chunk 数据、查询集
- `schemas/`
  治理表 schema 和日志字段说明
- `scripts/`
  初始化、导入、导出、分类、实验、指标汇总脚本
- `runs/`
  每次实验的原始日志和指标

### `skills/`

沉淀出的四个 skill 原型：

- [`memory-classify`](./skills/memory-classify/SKILL.md)
- [`memory-guard`](./skills/memory-guard/SKILL.md)
- [`memory-audit`](./skills/memory-audit/SKILL.md)
- [`memory-sandbox-share`](./skills/memory-sandbox-share/SKILL.md)

## 复现实验

环境要求：

- `python3`
- 本地已安装 OpenClaw
- 本地 `~/.openclaw/workspace-*/memory/*.md` 可读

### 1. 运行半合成样例实验

```bash
python3 experiments/scripts/init_governance_db.py
python3 experiments/scripts/seed_dataset.py

python3 experiments/scripts/run_baseline.py --run-id baseline_v1
python3 experiments/scripts/compute_metrics.py --run-id baseline_v1

python3 experiments/scripts/run_guarded.py --run-id guarded_v1
python3 experiments/scripts/compute_metrics.py --run-id guarded_v1
```

### 2. 导出真实 OpenClaw 记忆

```bash
python3 experiments/scripts/export_openclaw_memories.py
python3 experiments/scripts/classify_real_memories.py
```

### 3. 生成真实 chunk 数据

```bash
python3 experiments/scripts/chunk_real_memories.py
```

### 4. 运行真实 chunk 对照实验

```bash
python3 experiments/scripts/init_governance_db.py --db experiments/governance_real_chunks.sqlite
python3 experiments/scripts/seed_dataset.py \
  --db experiments/governance_real_chunks.sqlite \
  --dataset experiments/datasets/real_memory_chunks.jsonl

python3 experiments/scripts/run_baseline.py \
  --dataset experiments/datasets/real_memory_chunks.jsonl \
  --queries experiments/datasets/real_chunk_query_set.jsonl \
  --run-id real_chunk_baseline_v1

python3 experiments/scripts/run_guarded.py \
  --dataset experiments/datasets/real_memory_chunks.jsonl \
  --queries experiments/datasets/real_chunk_query_set.jsonl \
  --db experiments/governance_real_chunks.sqlite \
  --run-id real_chunk_guarded_v2

python3 experiments/scripts/compute_metrics.py \
  --run-id real_chunk_guarded_v2 \
  --queries experiments/datasets/real_chunk_query_set.jsonl
```

## Skills 使用

本仓库中的 skill 原型已经同步安装到本地用户技能目录：

- [`~/.codex/skills/memory-classify`](/Users/fairme/.codex/skills/memory-classify)
- [`~/.codex/skills/memory-guard`](/Users/fairme/.codex/skills/memory-guard)
- [`~/.codex/skills/memory-audit`](/Users/fairme/.codex/skills/memory-audit)
- [`~/.codex/skills/memory-sandbox-share`](/Users/fairme/.codex/skills/memory-sandbox-share)

### `memory-classify`

```bash
python3 ~/.codex/skills/memory-classify/scripts/classify_openclaw_memory.py \
  --output /tmp/openclaw_chunks.jsonl \
  --mode chunk
```

### `memory-guard`

```bash
python3 ~/.codex/skills/memory-guard/scripts/guard_memory_retrieval.py \
  --dataset /tmp/openclaw_chunks.jsonl \
  --queries /Users/fairme/Codes/openclaw-personalized-memory/experiments/datasets/real_chunk_query_set.jsonl \
  --run-dir /tmp/memory_guard_run
```

### `memory-audit`

```bash
python3 ~/.codex/skills/memory-audit/scripts/compute_memory_metrics.py \
  --run-dir /tmp/memory_guard_run \
  --queries /Users/fairme/Codes/openclaw-personalized-memory/experiments/datasets/real_chunk_query_set.jsonl
```

### `memory-sandbox-share`

```bash
python3 ~/.codex/skills/memory-sandbox-share/scripts/sandbox_share.py \
  --dataset /tmp/openclaw_chunks.jsonl \
  --query-id demo \
  --agent-id content \
  --purpose external_share \
  --chunk-ids <chunk_id> \
  --output /tmp/sandbox_results.jsonl
```

## 当前边界

本仓库目前验证的是“外挂式治理层”，不是直接修改 OpenClaw 核心。

已验证有效的部分：

- chunk 化
- 分级分类
- 策略前置
- 域隔离
- `L2` 摘要优先
- 审计留痕

尚未完整实现的部分：

- 完整 OpenClaw 内核接线
- 真实 OPA / OpenFGA 集成
- 真实 gVisor / Firecracker 沙箱
- 差分隐私同步闭环

## 建议的下一步

1. 将真实查询集换成你的日常高频使用场景
2. 细化 `L2` 摘要生成逻辑
3. 将 `memory-guard` 接到真实 OpenClaw 检索路径前
4. 按需接入 OPA / OpenFGA 做策略外置
