# Skills Package

本目录提供四个可复用的 memory governance skill 原型：

- `memory-classify`
- `memory-guard`
- `memory-audit`
- `memory-sandbox-share`

## 适用范围

当前更适合：

- 本地 OpenClaw 记忆治理实验
- 原型验证与研究复现
- 作为二次开发起点

当前还不适合直接视为生产级发布包，原因包括：

- 仍依赖本地 `~/.openclaw`
- 真实沙箱仍未接入
- 真实双设备同步仍未接入
- 真实 OpenClaw 内部检索链路仍未内核级集成

## 快速开始

### 1. 环境自检

```bash
python3 skills/check_skills_env.py
```

### 2. 安装到本地 Codex skills 目录

```bash
python3 skills/install_skills.py
```

默认会安装到：

```bash
~/.codex/skills
```

### 3. 最小 demo

```bash
python3 skills/memory-classify/scripts/classify_openclaw_memory.py \
  --output /tmp/openclaw_chunks.jsonl \
  --mode chunk

python3 skills/memory-guard/scripts/guard_memory_retrieval.py \
  --dataset /tmp/openclaw_chunks.jsonl \
  --queries experiments/datasets/real_chunk_query_set.jsonl \
  --run-dir /tmp/memory_guard_run

python3 skills/memory-audit/scripts/compute_memory_metrics.py \
  --run-dir /tmp/memory_guard_run \
  --queries experiments/datasets/real_chunk_query_set.jsonl
```

