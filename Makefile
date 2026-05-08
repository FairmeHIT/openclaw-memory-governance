PYTHON := python3

.PHONY: help \
	init seed baseline guarded metrics \
	export-real classify-real chunk-real \
	real-chunk-db real-chunk-baseline real-chunk-guarded real-chunk-guarded-light real-chunk-metrics \
	classifier-eval sandbox-eval openclaw-guard-demo native-fts-status \
	native-fts-ensure native-fts-validate openclaw-guarded-search-demo \
	install-openclaw-guarded-shim sync-eval local-dual-sync-eval attack-eval story-evals report-pack \
	skills-check skills-install \
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
	@echo "  real-chunk-guarded-light Run real chunk guarded-light experiment"
	@echo "  real-chunk-metrics   Compute real chunk baseline and guarded metrics"
	@echo "  classifier-eval      Evaluate classifier against the gold chunk set"
	@echo "  sandbox-eval         Run sandbox evaluation across raw/summary/sandbox modes"
	@echo "  story-evals          Run story-oriented innovation support experiments"
	@echo "  openclaw-guard-demo  Run native-first OpenClaw guard adapter demo"
	@echo "  openclaw-guarded-search-demo  Run guarded replacement for \`openclaw memory search\`"
	@echo "  install-openclaw-guarded-shim Install a local guarded search shim into ~/.local/bin"
	@echo "  sync-eval            Run simulated cross-device sync evaluation"
	@echo "  local-dual-sync-eval Run single-host dual-device sync/revoke evaluation"
	@echo "  attack-eval          Run attack-oriented retrieval evaluation"
	@echo "  report-pack          Generate report-ready data tables"
	@echo "  skills-check         Check whether the local environment is ready for the repo skills"
	@echo "  skills-install       Install repo skills into ~/.codex/skills"
	@echo "  native-fts-status    Show env-scrubbed OpenClaw memory status for assistant"
	@echo "  native-fts-ensure    Rebuild native FTS indexes for all default agents"
	@echo "  native-fts-validate  Restore and validate native FTS across agents"
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

real-chunk-guarded-light:
	rm -rf experiments/runs/real_chunk_guarded_light_v1
	$(PYTHON) experiments/scripts/run_guarded.py \
		--dataset experiments/datasets/real_memory_chunks.jsonl \
		--queries experiments/datasets/real_chunk_query_set.jsonl \
		--db experiments/governance_real_chunks.sqlite \
		--policy-mode light \
		--run-id real_chunk_guarded_light_v1

real-chunk-metrics:
	$(PYTHON) experiments/scripts/compute_metrics.py --run-id real_chunk_baseline_v1 --queries experiments/datasets/real_chunk_query_set.jsonl
	$(PYTHON) experiments/scripts/compute_metrics.py --run-id real_chunk_guarded_light_v1 --queries experiments/datasets/real_chunk_query_set.jsonl
	$(PYTHON) experiments/scripts/compute_metrics.py --run-id real_chunk_guarded_v2 --queries experiments/datasets/real_chunk_query_set.jsonl

classifier-eval:
	rm -rf experiments/runs/classifier_eval_v2
	$(PYTHON) experiments/scripts/evaluate_classifier.py \
		--gold experiments/datasets/classification_gold.jsonl \
		--predicted experiments/datasets/real_memory_chunks.jsonl \
		--run-id classifier_eval_v2

sandbox-eval:
	rm -rf experiments/runs/sandbox_eval_v1
	$(PYTHON) experiments/scripts/run_sandbox_eval.py --run-id sandbox_eval_v1

openclaw-guard-demo:
	rm -rf experiments/runs/openclaw_guard_native_demo
	$(PYTHON) experiments/scripts/openclaw_guard_adapter.py \
		--agent assistant \
		--purpose personalization \
		--query "AI 新闻" \
		--run-id openclaw_guard_native_demo

openclaw-guarded-search-demo:
	rm -rf experiments/runs/openclaw_guarded_search_demo
	$(PYTHON) experiments/scripts/openclaw_memory_search_guarded.py \
		--agent assistant \
		--purpose personalization \
		--json \
		--query "AI 新闻" \
		--run-id openclaw_guarded_search_demo

install-openclaw-guarded-shim:
	$(PYTHON) experiments/scripts/install_openclaw_guarded_shim.py

sync-eval:
	rm -rf experiments/runs/sync_eval_v1
	$(PYTHON) experiments/scripts/run_sync_eval.py --run-id sync_eval_v1

local-dual-sync-eval:
	rm -rf experiments/runs/local_dual_device_sync_v1
	$(PYTHON) experiments/scripts/run_local_dual_device_sync.py --run-id local_dual_device_sync_v1

attack-eval: real-chunk-db
	rm -rf experiments/runs/attack_eval_v1
	$(PYTHON) experiments/scripts/run_attack_eval.py --run-id attack_eval_v1

story-evals: real-chunk-db
	rm -rf experiments/runs/objectization_eval_v1
	$(PYTHON) experiments/scripts/run_objectization_eval.py --run-id objectization_eval_v1
	rm -rf experiments/runs/pre_guard_vs_post_filter_v1
	$(PYTHON) experiments/scripts/run_pre_guard_vs_post_filter.py --run-id pre_guard_vs_post_filter_v1
	rm -rf experiments/runs/output_shape_eval_v1
	$(PYTHON) experiments/scripts/run_output_shape_eval.py --run-id output_shape_eval_v1
	rm -rf experiments/runs/story_trace_v1
	$(PYTHON) experiments/scripts/run_story_trace.py --run-id story_trace_v1
	rm -rf experiments/runs/local_dual_device_sync_v1
	$(PYTHON) experiments/scripts/run_local_dual_device_sync.py --run-id local_dual_device_sync_v1

report-pack: story-evals attack-eval
	rm -rf experiments/runs/report_pack_v1
	$(PYTHON) experiments/scripts/generate_report_pack.py --run-id report_pack_v1

skills-check:
	$(PYTHON) skills/check_skills_env.py

skills-install:
	$(PYTHON) skills/install_skills.py

native-fts-status:
	$(PYTHON) experiments/scripts/openclaw_fts_only.py status --agent assistant --deep --json

native-fts-ensure:
	$(PYTHON) experiments/scripts/openclaw_fts_only.py ensure \
		--output experiments/runs/native_fts_ensure/summary.json

native-fts-validate:
	rm -rf experiments/runs/native_fts_validation_v5
	$(PYTHON) experiments/scripts/validate_openclaw_native_fts.py --run-id native_fts_validation_v5

skill-classify-demo:
	$(PYTHON) ~/.codex/skills/memory-classify/scripts/classify_openclaw_memory.py \
		--output experiments/datasets/generated/skill_chunk_output.jsonl \
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
