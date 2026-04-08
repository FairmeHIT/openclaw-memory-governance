# OpenClaw Integration

本文档说明如何把当前仓库的 `memory-guard` 原型接到真实 OpenClaw 检索链路前，并记录当前环境下的实际限制。

## 1. 当前环境观察

本机 OpenClaw 安装路径：

- `~/.openclaw/`
- `~/.npm-global/lib/node_modules/openclaw/`

已经确认的真实切入点：

- OpenClaw CLI 暴露了 `openclaw memory search`
- 每个 agent 对应一个内建 memory SQLite
- 路径格式：
  - `~/.openclaw/memory/main.sqlite`
  - `~/.openclaw/memory/assistant.sqlite`
  - `~/.openclaw/memory/code.sqlite`
  - `~/.openclaw/memory/content.sqlite`
  - `~/.openclaw/memory/zhixi.sqlite`

SQLite schema 中的关键表：

- `files`
- `chunks`
- `chunks_fts`
- `embedding_cache`

这说明最小侵入接线不需要改 OpenClaw 核心，只要在真实候选 chunk 返回前插入治理判断即可。

## 2. 真实恢复路径

当前机器上，默认 auto provider 会优先命中远程 embeddings，因此原生 `memory index` 最开始会因为外部连接失败。

但 builtin engine 文档同时说明：没有 embedding provider 时，OpenClaw 会退回 `fts-only`。

本机已验证下面的恢复方式可行：

```bash
env -u OPENAI_API_KEY -u GEMINI_API_KEY -u VOYAGE_API_KEY -u MISTRAL_API_KEY \
  openclaw memory status --deep --agent assistant --json
```

此时关键状态会变为：

- `provider = none`
- `searchMode = fts-only`

随后可成功执行：

```bash
env -u OPENAI_API_KEY -u GEMINI_API_KEY -u VOYAGE_API_KEY -u MISTRAL_API_KEY \
  openclaw memory index --agent assistant --force
```

当前 assistant SQLite 已验证写入：

- `files = 4`
- `chunks = 10`
- `chunks_fts = 10`

为了避免继续手工写 `env -u ...`，仓库里已经补了正式包装脚本：

- [`openclaw_fts_only.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/openclaw_fts_only.py)

## 3. 当前剩余限制

虽然 FTS-only 已恢复，但还有一个限制：

1. 默认 auto provider 仍会优先探测外部 embeddings，需要显式清理 env 才会退回 `fts-only`

## 4. 已实现的最小接线层

新增脚本：

- [`openclaw_guard_adapter.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/openclaw_guard_adapter.py)
- [`openclaw_memory_search_guarded.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/openclaw_memory_search_guarded.py)
- [`install_openclaw_guarded_shim.py`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/install_openclaw_guarded_shim.py)

它的行为是：

1. 先用 `memory-classify` skill 对 `~/.openclaw/workspace-*/memory/*.md` 生成 chunk 级治理数据
2. 优先读取真实 OpenClaw SQLite `chunks/chunks_fts`
3. 如果原生 index 为空或不可用，则回退到本地 chunk 检索
4. 对候选集执行 `allow / deny / downgrade / sandbox`
5. 输出与实验脚本一致的治理日志：
   - `policy_decisions.jsonl`
   - `retrieval_hits.jsonl`
   - `audit_events.jsonl`
   - `sandbox_jobs.jsonl`

在适配层之上，现在又补了一层可直接替代 CLI 的 guarded search wrapper：

- `openclaw_memory_search_guarded.py`

它尽量对齐 `openclaw memory search` 的参数习惯：

- 支持位置参数 `query`
- 支持 `--query`
- 支持 `--agent`
- 支持 `--max-results`
- 支持 `--json`

同时增加治理上下文：

- `--purpose`
- `--run-id`

## 5. 使用方式

示例：

```bash
python3 experiments/scripts/openclaw_fts_only.py status --agent assistant --deep --json

python3 experiments/scripts/openclaw_fts_only.py index --agent assistant --force

python3 experiments/scripts/openclaw_fts_only.py search \
  --agent assistant \
  --json \
  --query "AI 新闻" \
  --max-results 5

python3 experiments/scripts/openclaw_fts_only.py ensure \
  --output experiments/runs/native_fts_ensure/summary.json

python3 experiments/scripts/openclaw_guard_adapter.py \
  --agent assistant \
  --purpose personalization \
  --query "我最近在哪个区域出差？" \
  --run-id openclaw_guard_native_demo

python3 experiments/scripts/openclaw_memory_search_guarded.py \
  --agent assistant \
  --purpose personalization \
  --json \
  --query "AI 新闻" \
  --run-id openclaw_guarded_search_demo

python3 experiments/scripts/install_openclaw_guarded_shim.py

~/.local/bin/openclaw-memory-search-guarded \
  --agent assistant \
  --purpose personalization \
  --json \
  --query "AI 新闻"
```

输出目录：

- `experiments/runs/openclaw_guard_native_demo/`

关键返回字段：

- `candidate_source`
  - `native_cli`
  - `native_fts`
  - `fallback:empty_index`
  - `fallback:missing_db`
  - `fallback:native_error:*`
- `allowed`
- `downgraded`
- `sandboxed`
- `denied`

已验证的真实 native 候选 demo：

```bash
python3 experiments/scripts/openclaw_guard_adapter.py \
  --agent assistant \
  --purpose personalization \
  --query "AI 新闻" \
  --run-id openclaw_guard_native_demo
```

返回：

- `candidate_source = native_cli`

全量验证结果：

- [`native_fts_query_set.jsonl`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/datasets/native_fts_query_set.jsonl)
- [`metrics.json`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/native_fts_validation_v5/metrics.json)
- [`details.jsonl`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/native_fts_validation_v5/details.jsonl)

关键指标：

- `agents_with_index_rows = 5`
- `native_search_success_rate = 1.0`
- `guard_native_cli_rate = 1.0`

## 6. 为什么先做适配层

这是当前最稳的路径，因为它满足三点：

1. 不修改 OpenClaw 安装包
2. 一旦原生 index 可用，可直接消费真实 `chunks` 结果
3. 当前即使原生 index 为空，也能维持真实治理接口和审计格式

## 7. 下一步

如果要把这一步从“适配层”推进到“真正集成”，建议顺序是：

1. 让上层调用优先使用 `openclaw-memory-search-guarded` shim
2. 再决定是否需要改 OpenClaw 安装包内部实现
3. 如果要长期维护，再补最终集成补丁说明
