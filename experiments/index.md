# Experiments

本目录用于承载个性化记忆治理原型验证所需的实验资产。

## 目录约定

- `datasets/`
  - 记忆样本、人工标注和测试查询
  - 见 [`datasets/index.md`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/datasets/index.md)
- `schemas/`
  - SQLite schema、日志 schema、字段说明
- `scripts/`
  - 数据导入、分类、实验运行、指标汇总脚本
  - 见 [`scripts/guide.md`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/scripts/guide.md)
- `runs/`
  - 每次实验的原始日志与指标输出
  - 见 [`runs/index.md`](/Users/fairme/Codes/openclaw-personalized-memory/experiments/runs/index.md)
- `reports/`
  - 汇总结论、图表和案例分析

## 实施顺序

1. 准备样例记忆数据和人工标注
2. 建立治理元数据表
3. 接入分类器
4. 接入检索前策略判定
5. 运行基线对照实验
6. 运行沙箱与同步等扩展实验
