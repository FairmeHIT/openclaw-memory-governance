# Repository Structure

本文件约束仓库后续文件组织方式，避免文档、实验资产和可执行原型继续混放。

## 1. 顶层目录职责

- `README.md`
  GitHub 首页，只保留项目概览、关键结果、快速入口和文档导航。
- `content.md`
  研究报告原文，不放运行说明和仓库维护信息。
- `docs/`
  结构化文档。
- `experiments/`
  数据集、schema、脚本、runs、发布快照、报告。
- `skills/`
  对外可复用的 skill 包。
- `prototype/`
  预留给后续内核级或更系统化实现，不再放实验日志或说明性文档。

## 2. docs 目录约定

- `architecture.md`
  架构分层和数据流。
- `github-analysis.md`
  相关项目调研与选型分析。
- `validation-plan.md`
  原型验证方案。
- `openclaw-integration.md`
  与真实 OpenClaw 的接线说明。
- `skill-usage.md`
  skill 使用说明。
- `todo.md`
  仅保留真实未完成项。
- `repository-structure.md`
  仓库组织规范。

## 3. experiments 目录约定

- `index.md`
  实验目录入口。
- `datasets/`
  可版本化的数据集、查询集、gold 集。
  其中 `generated/` 用于可再生产物。
- `schemas/`
  SQL schema、日志 schema、字段定义。
- `scripts/`
  可执行实验脚本和脚本使用说明。
- `runs/`
  原始运行输出。
  其中 `archive/` 用于历史验证迭代和 demo。
- `reports/`
  结论性报告。
- `releases/`
  固定引用的发布快照。

## 4. 命名约定

- 目录入口文档优先使用：
  - `index.md`
  - `guide.md`
  - `overview.md`
  - `package.md`
- 避免在多个子目录继续增加泛化的 `README.md`。
- 脚本文件统一用动词开头：
  - `run_*`
  - `compute_*`
  - `export_*`
  - `install_*`
  - `validate_*`

## 5. 新文件放置规则

- 如果文件主要解释“怎么用仓库”，放 `docs/`
- 如果文件主要支撑“怎么复现实验”，放 `experiments/`
- 如果文件主要用于“对外安装或分发 skill”，放 `skills/`
- 如果文件只是某次运行结果，放 `experiments/runs/`
- 如果是旧验证版本或临时 demo，优先移动到 `experiments/runs/archive/`
- 如果文件是稳定引用结果，拷贝到 `experiments/releases/`

## 6. 当前整理动作

本轮整理已经做了这些收敛：

- `docs/prototype-validation-plan.md` -> `docs/validation-plan.md`
- `experiments/README.md` -> `experiments/index.md`
- `experiments/scripts/README.md` -> `experiments/scripts/guide.md`
- `experiments/releases/v1/README.md` -> `experiments/releases/v1/index.md`
- `prototype/README.md` -> `prototype/overview.md`
- `skills/README.md` -> `skills/package.md`
