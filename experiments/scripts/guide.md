# Scripts

当前已提供：

- `init_governance_db.py`
  - 初始化治理数据库和表
- `seed_dataset.py`
  - 将 `memory_samples.jsonl` 导入治理数据库
- `run_baseline.py`
  - 跑不带治理层的基线实验
- `run_guarded.py`
  - 跑带静态策略拦截的实验
  - 支持 `--policy-mode full|light`
- `compute_metrics.py`
  - 从 JSONL 日志汇总指标
- `run_sandbox_eval.py`
  - 跑高敏记忆的 raw / summary / sandbox 对照
- `run_sync_eval.py`
  - 跑模拟跨设备同步的 local / raw / summary / dp 对照

推荐运行顺序：

1. `python3 experiments/scripts/init_governance_db.py`
2. `python3 experiments/scripts/seed_dataset.py`
3. `python3 experiments/scripts/run_baseline.py --run-id baseline_v1`
4. `python3 experiments/scripts/compute_metrics.py --run-id baseline_v1`
5. `python3 experiments/scripts/run_guarded.py --run-id guarded_v1`
6. `python3 experiments/scripts/compute_metrics.py --run-id guarded_v1`

第一版使用规则检索和静态策略，不依赖额外第三方库。
