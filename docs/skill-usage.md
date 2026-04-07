# Skill Usage

本文档说明本仓库中 memory governance skills 的职责、输入输出和最小使用方式。

## Skills 列表

### `memory-classify`

用途：

- 从 OpenClaw `workspace-*/memory/*.md` 提取记忆
- 生成 file-level 或 chunk-level 治理对象
- 为对象打上治理标签

主要脚本：

- [`classify_openclaw_memory.py`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-classify/scripts/classify_openclaw_memory.py)

最小调用：

```bash
python3 ~/.codex/skills/memory-classify/scripts/classify_openclaw_memory.py \
  --output /tmp/openclaw_chunks.jsonl \
  --mode chunk
```

输出字段重点：

- `chunk_id`
- `memory_id`
- `agent_id`
- `workspace`
- `domain`
- `raw_text`
- `retrieval_text`
- `privacy_level`
- `purpose_allow`
- `lifecycle`
- `sync_policy`
- `index_policy`

### `memory-guard`

用途：

- 在候选记忆命中后、返回前做策略裁剪
- 输出 allow / deny / downgrade / sandbox

主要脚本：

- [`guard_memory_retrieval.py`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-guard/scripts/guard_memory_retrieval.py)

最小调用：

```bash
python3 ~/.codex/skills/memory-guard/scripts/guard_memory_retrieval.py \
  --dataset /tmp/openclaw_chunks.jsonl \
  --queries /path/to/query_set.jsonl \
  --run-dir /tmp/memory_guard_run
```

输出文件：

- `policy_decisions.jsonl`
- `retrieval_hits.jsonl`
- `audit_events.jsonl`
- `sandbox_jobs.jsonl`

当前默认策略：

- 跨域默认拒绝
- `shared` 可跨域
- `L3` 默认 `sandbox` 或拒绝
- `L2` 默认 `downgrade`
- `external_share` 对 `L2/L3` 不返回原文

### `memory-audit`

用途：

- 从运行日志计算核心治理指标

主要脚本：

- [`compute_memory_metrics.py`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-audit/scripts/compute_memory_metrics.py)

最小调用：

```bash
python3 ~/.codex/skills/memory-audit/scripts/compute_memory_metrics.py \
  --run-dir /tmp/memory_guard_run \
  --queries /path/to/query_set.jsonl
```

输出：

- `metrics.json`

当前指标：

- `task_success_rate`
- `unauthorized_recall_rate`
- `sensitive_raw_exposure_rate`
- `cross_domain_leak_count`
- `policy_enforcement_rate`
- `policy_eval_latency_ms_p50`
- `policy_eval_latency_ms_p95`

### `memory-sandbox-share`

用途：

- 对高敏 chunk 做 summary-only 输出
- 模拟沙箱共享模式

主要脚本：

- [`sandbox_share.py`](/Users/fairme/Codes/openclaw-personalized-memory/skills/memory-sandbox-share/scripts/sandbox_share.py)

最小调用：

```bash
python3 ~/.codex/skills/memory-sandbox-share/scripts/sandbox_share.py \
  --dataset /tmp/openclaw_chunks.jsonl \
  --query-id demo \
  --agent-id content \
  --purpose external_share \
  --chunk-ids <chunk_id> \
  --output /tmp/sandbox_results.jsonl
```

输出字段重点：

- `job_id`
- `request_id`
- `agent_id`
- `chunk_id`
- `input_privacy_levels`
- `output_mode`
- `raw_output_blocked`
- `status`
- `summary`

## 推荐调用顺序

最小闭环建议按下面顺序运行：

1. `memory-classify`
2. `memory-guard`
3. `memory-audit`

若请求命中高敏内容，再加：

4. `memory-sandbox-share`

## 当前适用范围

这些 skills 当前适合：

- OpenClaw 本地工作区记忆治理实验
- 多 workspace 场景下的域隔离验证
- 高敏记忆的摘要优先输出实验
- 研究报告配套原型与指标评估

当前不适合直接视为生产完成方案，原因包括：

- 仍是外挂式集成
- 还未接真实 OpenClaw 内核检索路径
- 还未接外部授权和策略引擎
- 真实沙箱仍是逻辑模拟
