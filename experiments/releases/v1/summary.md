# Release V1 Summary

## 结论摘要

本次发布版结果支持以下结论：

1. 仅靠 OpenClaw 原始整文件记忆进行治理，粒度过粗。
2. 将 session 文件切成 chunk 后，记忆对象更适合做分级分类和策略控制。
3. 检索前域隔离可以把真实 chunk 实验中的跨域串扰降到 0。
4. 对 `L2` 默认使用摘要优先策略，可以把高敏原文暴露率压到 0，同时保持基本可用性。

## 推荐主结果

### 真实 chunk 基线

- `task_success_rate = 1.0`
- `unauthorized_recall_rate = 0.75`
- `sensitive_raw_exposure_rate = 0.25`
- `cross_domain_leak_count = 4`

来源：

- `real_chunk_baseline_metrics.json`

### 真实 chunk 治理版 v2

- `task_success_rate = 0.875`
- `unauthorized_recall_rate = 0.125`
- `sensitive_raw_exposure_rate = 0.0`
- `cross_domain_leak_count = 0`

来源：

- `real_chunk_guarded_v2_metrics.json`

## 对比解释

与基线相比，治理版 v2：

- 将跨域串扰从 `4` 降到 `0`
- 将高敏原文暴露率从 `0.25` 降到 `0.0`
- 将越权召回率从 `0.75` 降到 `0.125`
- 任务成功率从 `1.0` 降到 `0.875`

这表明：

- 安全性显著提升
- 可用性存在但可接受的损失
- 当前方案更适合以“summary-first + chunk-level governance”形态继续演进
