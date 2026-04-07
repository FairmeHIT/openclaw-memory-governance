PYTHON := python3

.PHONY: help \
	init seed baseline guarded metrics \
	export-real classify-real chunk-real \
	real-chunk-db real-chunk-baseline real-chunk-guarded real-chunk-metrics \
	skill-classify-demo skill-guard-demo skill-audit-demo skill-sandbox-demo

help:
	@echo "Targets:"
	@echo "  init                 Initialize sample governance DB"
	@echo "  seed                 Seed sample dataset into sample governance DB"
	@echo "  baseline             Run sample baseline experiment"
	@echo "  guarded              Run sample guarded experiment"
	@echo "  metrics              Compute sample baseline and guarded metrics"
	@echo "  export-real          Export real OpenClaw memory files"
	@echo "  classify-real        Label exported real OpenClaw memory files"
	@echo "  chunk-real           Split real OpenClaw memory into governed chunks"
	@echo "  real-chunk-db        Initialize and seed real chunk governance DB"
	@echo "  real-chunk-baseline  Run real chunk baseline experiment"
	@echo "  real-chunk-guarded   Run real chunk guarded v2 experiment"
	@echo "  real-chunk-metrics   Compute real chunk baseline and guarded metrics"
	@echo "  skill-classify-demo  Run memory-classify skill demo"
	@echo "  skill-guard-demo     Run memory-guard skill demo"
	@echo "  skill-audit-demo     Run memory-audit skill demo"
	@echo "  skill-sandbox-demo   Run memory-sandbox-share skill demo"

init:
	$(PYTHON) experiments/scripts/init_governance_db.py

seed:
	$(PYTHON) experiments/scripts/seed_dataset.py

baseline:
	$(PYTHON) experiments/scripts/run_baseline.py --run-id baseline_v1

guarded:
	$(PYTHON) experiments/scripts/run_guarded.py --run-id guarded_v1

metrics:
	$(PYTHON) experiments/scripts/compute_metrics.py --run-id baseline_v1
	$(PYTHON) experiments/scripts/compute_metrics.py --run-id guarded_v1

export-real:
	$(PYTHON) experiments/scripts/export_openclaw_memories.py

classify-real:
	$(PYTHON) experiments/scripts/classify_real_memories.py

chunk-real:
	$(PYTHON) experiments/scripts/chunk_real_memories.py

real-chunk-db:
	rm -f experiments/governance_real_chunks.sqlite
	$(PYTHON) experiments/scripts/init_governance_db.py --db experiments/governance_real_chunks.sqlite
	$(PYTHON) experiments/scripts/seed_dataset.py --db experiments/governance_real_chunks.sqlite --dataset experiments/datasets/real_memory_chunks.jsonl

real-chunk-baseline:
	rm -rf experiments/runs/real_chunk_baseline_v1
	$(PYTHON) experiments/scripts/run_baseline.py \
		--dataset experiments/datasets/real_memory_chunks.jsonl \
		--queries experiments/datasets/real_chunk_query_set.jsonl \
		--run-id real_chunk_baseline_v1

real-chunk-guarded:
	rm -rf experiments/runs/real_chunk_guarded_v2
	$(PYTHON) experiments/scripts/run_guarded.py \
		--dataset experiments/datasets/real_memory_chunks.jsonl \
		--queries experiments/datasets/real_chunk_query_set.jsonl \
		--db experiments/governance_real_chunks.sqlite \
		--run-id real_chunk_guarded_v2

real-chunk-metrics:
	$(PYTHON) experiments/scripts/compute_metrics.py --run-id real_chunk_baseline_v1 --queries experiments/datasets/real_chunk_query_set.jsonl
	$(PYTHON) experiments/scripts/compute_metrics.py --run-id real_chunk_guarded_v2 --queries experiments/datasets/real_chunk_query_set.jsonl

skill-classify-demo:
	$(PYTHON) ~/.codex/skills/memory-classify/scripts/classify_openclaw_memory.py \
		--output experiments/datasets/skill_chunk_output.jsonl \
		--mode chunk

skill-guard-demo:
	rm -rf experiments/runs/skill_guard_demo
	$(PYTHON) ~/.codex/skills/memory-guard/scripts/guard_memory_retrieval.py \
		--dataset experiments/datasets/real_memory_chunks.jsonl \
		--queries experiments/datasets/real_chunk_query_set.jsonl \
		--run-dir experiments/runs/skill_guard_demo

skill-audit-demo:
	$(PYTHON) ~/.codex/skills/memory-audit/scripts/compute_memory_metrics.py \
		--run-dir experiments/runs/real_chunk_guarded_v2 \
		--queries experiments/datasets/real_chunk_query_set.jsonl

skill-sandbox-demo:
	rm -rf experiments/runs/skill_sandbox_demo
	$(PYTHON) ~/.codex/skills/memory-sandbox-share/scripts/sandbox_share.py \
		--dataset experiments/datasets/real_memory_chunks.jsonl \
		--query-id demo_sbx_001 \
		--agent-id content \
		--purpose external_share \
		--chunk-ids chunk_d5b9eaeba12ab1ce chunk_b69a54ea3e0e4e43 \
		--output experiments/runs/skill_sandbox_demo/results.jsonl
