# TODO

本文档只保留当前仓库里仍未完成，或仅完成到原型级的工作项。

## 1. 当前结论

以下工作已经完成，不再作为 TODO：

- 真实 OpenClaw chunk 化实验
- 分类质量验证实验
- `L2` 摘要优先验证
- 风险对照实验 `baseline / guarded_light / guarded_v2`
- 高敏沙箱模拟评测
- 模拟跨设备同步评测
- native FTS 恢复与 guarded wrapper

## 2. 仍未完成

### 2.1 真实 OpenClaw 内部接线

现状：

- 已有 [openclaw_guard_adapter.py](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/openclaw_guard_adapter.py)
- 已有 [openclaw_memory_search_guarded.py](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/openclaw_memory_search_guarded.py)
- 已可通过本地 shim 替代 `openclaw memory search`

缺口：

- 还没有真正嵌入 OpenClaw 安装包内部的真实 tool 返回前

建议下一步：

1. 定位 OpenClaw 内部实际返回检索结果的位置
2. 在候选结果返回前插入治理判断
3. 补最小内部集成补丁说明

### 2.2 真实隔离沙箱

现状：

- 已有 `baseline_raw / summary_only / sandbox_job` 三组对照
- 已有模拟 `sandbox_overhead_ms_p50 = 2.518`

缺口：

- 仍是模拟受控分析器，不是真实隔离执行环境

建议下一步：

1. 用真实 sandbox runtime 替换当前模拟逻辑
2. 记录真实 job lifecycle 和开销
3. 复跑 `sandbox_eval_v1`

### 2.3 真实双设备同步

现状：

- 已有模拟 `local_only / raw_sync / summary_sync / dp_sync`
- 已能给出 `personalization_gain`、`reidentification_risk_score`、`sync_overhead_ms_p50`

缺口：

- 还没接真实双设备数据流
- `dp_sync` 仍是摘要级近似模拟，不是严格 DP 训练/聚合

建议下一步：

1. 准备真实双设备样本
2. 把 `run_sync_eval.py` 迁到更接近真实同步路径
3. 引入更严格的 DP/噪声机制
4. 增加重识别攻击评测

### 2.4 外置策略引擎接入

现状：

- 已完成 OPA / OpenFGA 调研

缺口：

- 还没有正式实现

建议下一步：

1. 先接 OPA 表达 usage control
2. 再接 OpenFGA 表达跨域访问关系
3. 跑一次内嵌规则 vs 外置策略引擎对照

## 3. 次级收尾

### 3.1 指标统一

现状：

- 主实验已统一输出大部分指标
- 同步实验有自己的 `sync_overhead_ms_p50`

缺口：

- 还没把同步类指标完全并入主 `compute_metrics.py` 口径

### 3.2 报告与发布同步

现状：

- [final-report.md](/Users/fairme/Codes/openclaw-personalized-memory/experiments/reports/final-report.md) 已更新
- [README.md](/Users/fairme/Codes/openclaw-personalized-memory/README.md) 已压缩为首页版

缺口：

- 后续如果继续做真实内核接线 / 真实沙箱 / 真实双设备同步，需要同步更新 release 快照

## 4. 推荐顺序

建议后续按这个顺序继续：

1. 真实 OpenClaw 内部接线
2. 真实隔离沙箱
3. 真实双设备同步
4. 外置策略引擎接入
