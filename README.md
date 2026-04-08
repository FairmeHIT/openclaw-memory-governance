# OpenClaw Memory Governance

基于 OpenClaw 本地基线的个性化记忆治理原型验证仓库。

这个仓库验证的不是“重做一个 memory store”，而是一套治理闭环是否有效：
- chunk 级记忆分类
- 检索前策略判定
- personal / work / third-party 域隔离
- `L2` 摘要优先
- `L3` 受控分析
- 审计日志与指标验证
- 脱敏同步而非原文同步

## 核心结论

在真实 OpenClaw chunk 实验中：
- `cross_domain_leak_count` 从 `4` 降到 `0`
- `sensitive_raw_exposure_rate` 从 `0.25` 降到 `0.0`
- `task_success_rate` 保持在 `0.875`

风险对照实验表明：
- 轻量策略已经足够消除跨域串扰
- 完整策略的增量价值主要来自 `L2` 摘要优先和高敏受控输出

同步实验表明：
- `raw_sync` 收益高，但重识别风险高
- `summary_sync` 在当前样例里保住了同等任务成功率，同时把风险压到 `0.0`

## 关键结果

### 真实 chunk 三组对照

| Run | task_success_rate | unauthorized_recall_rate | sensitive_raw_exposure_rate | cross_domain_leak_count |
|---|---:|---:|---:|---:|
| `real_chunk_baseline_v1` | 1.0 | 0.75 | 0.25 | 4 |
| `real_chunk_guarded_light_v1` | 0.875 | 0.125 | 0.25 | 0 |
| `real_chunk_guarded_v2` | 0.875 | 0.125 | 0.0 | 0 |

### 高敏沙箱对照

| Mode | raw_exposure_rate | task_success_rate | sandbox_overhead_ms_p50 |
|---|---:|---:|---:|
| `baseline_raw` | 1.0 | 1.0 | 0.0 |
| `summary_only` | 0.0 | 0.6667 | 0.0 |
| `sandbox_job` | 0.0 | 1.0 | 2.518 |

### 模拟同步对照

| Mode | task_success_rate | personalization_gain | reidentification_risk_score |
|---|---:|---:|---:|
| `local_only` | 0.0 | 0.0 | 0.0 |
| `raw_sync` | 1.0 | 1.0 | 0.95 |
| `summary_sync` | 1.0 | 1.0 | 0.0 |
| `dp_sync` | 0.6667 | 0.6667 | 0.0 |

## 快速开始

先看可用命令：

```bash
make help
```

常用入口：

```bash
make real-chunk-db
make real-chunk-baseline
make real-chunk-guarded-light
make real-chunk-guarded
make real-chunk-metrics
make sandbox-eval
make sync-eval
make native-fts-validate
make openclaw-guarded-search-demo
```

如果要安装可替代 `openclaw memory search` 的本地入口：

```bash
make install-openclaw-guarded-shim
~/.local/bin/openclaw-memory-search-guarded --agent assistant --purpose personalization --json --query "AI 新闻"
```

如果要安装仓库里的四个 memory governance skills：

```bash
make skills-check
make skills-install
```

## 仓库导航

核心文档：
- [研究报告](./content.md)
- [GitHub 调研分析](./docs/github-analysis.md)
- [原型验证方案](./docs/validation-plan.md)
- [最终报告](./experiments/reports/final-report.md)
- [架构说明](./docs/architecture.md)
- [OpenClaw 接线说明](./docs/openclaw-integration.md)
- [Skill 使用文档](./docs/skill-usage.md)
- [仓库结构规范](./docs/repository-structure.md)

实验与结果：
- [实验目录](./experiments/index.md)
- [发布快照](./experiments/releases/v1/index.md)
- [真实 chunk baseline 指标](./experiments/runs/real_chunk_baseline_v1/metrics.json)
- [真实 chunk light 指标](./experiments/runs/real_chunk_guarded_light_v1/metrics.json)
- [真实 chunk guarded 指标](./experiments/runs/real_chunk_guarded_v2/metrics.json)
- [沙箱评测指标](./experiments/runs/sandbox_eval_v1/metrics.json)
- [同步评测指标](./experiments/runs/sync_eval_v1/metrics.json)

可复用能力原型：
- [skills package 说明](./skills/package.md)
- [memory-classify](./skills/memory-classify/SKILL.md)
- [memory-guard](./skills/memory-guard/SKILL.md)
- [memory-audit](./skills/memory-audit/SKILL.md)
- [memory-sandbox-share](./skills/memory-sandbox-share/SKILL.md)

## 当前边界

当前实现已经有真实 native FTS 接线和 guarded wrapper，但还没有直接修改 OpenClaw 安装包内部检索实现。沙箱和 DP 同步也仍是原型级验证，不是生产级集成。
