# Release V1

本目录收录第一轮原型验证的发布版结果。

目标：

- 固定一组可引用的实验结果
- 避免后续迭代覆盖关键结论
- 为汇报、论文附录、对外展示提供稳定材料

## 内容

- `sample_baseline_metrics.json`
- `sample_guarded_metrics.json`
- `real_file_baseline_metrics.json`
- `real_file_guarded_metrics.json`
- `real_chunk_baseline_metrics.json`
- `real_chunk_guarded_v1_metrics.json`
- `real_chunk_guarded_v2_metrics.json`
- `real_chunk_guarded_v2_policy_decisions.jsonl`
- `real_chunk_guarded_v2_retrieval_hits.jsonl`
- `skill_sandbox_demo_results.jsonl`
- `summary.md`

## 推荐引用

如果只引用一组最终结果，优先使用：

- `real_chunk_baseline_metrics.json`
- `real_chunk_guarded_v2_metrics.json`

这是当前仓库中最接近“真实 OpenClaw + chunk 级治理 + L2 摘要优先”的结果。
