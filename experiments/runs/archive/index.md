# Runs Archive

本目录用于保存两类不应继续堆在 `experiments/runs/` 顶层的结果：

- `validation/`
  历史验证迭代，例如 `native_fts_validation_v1-v4`
- `demo/`
  临时 demo、本地 shim 演示、skill 演示

原则：

- 当前 README、最终报告、release 正在引用的结果，保留在 `experiments/runs/` 顶层
- 已被后续版本替代、且仍有保留价值的结果，移入 `archive/`
