# Runs Index

本目录分三层管理：

- 顶层：
  当前仍在文档、README、报告中直接引用的关键结果
- `archive/validation/`
  历史验证迭代结果，例如 `native_fts_validation_v1-v4`
- `archive/demo/`
  临时 demo、shim 演示和本地 skill demo

## 当前保留在顶层的关键结果

- `real_chunk_baseline_v1`
- `real_chunk_guarded_light_v1`
- `real_chunk_guarded_v2`
- `sandbox_eval_v1`
- `sync_eval_v1`
- `native_fts_validation_v5`
- `openclaw_guard_native_demo`
- `openclaw_guarded_search_demo`

## 归档说明

如果某个 run：

- 不再被 README 或最终报告引用
- 只是中间调试版本
- 可以由当前脚本重新生成

则优先移动到 `archive/`，不要继续堆在顶层。
