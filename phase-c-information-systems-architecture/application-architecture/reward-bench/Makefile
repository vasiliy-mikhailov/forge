# reward-bench/Makefile — agentic comprehensiveness benchmark.
# Per ADR 0029 + SPEC.md.

include $(shell git rev-parse --show-toplevel)/common.mk

# Per-tier image tag — bumped per ADR amendment.
TIER1_IMAGE := reward-bench-tier1:0.1
LAB_DIR     := $(shell pwd)
EXPERIMENTS := $(STORAGE_ROOT)/labs/reward-bench/experiments

.PHONY: help build-tier1 smoke-tier1 shim claude-fixture-tier1 attempt clean

help:
	@echo "reward-bench — agentic comprehensiveness benchmark"
	@echo ""
	@echo "Build:"
	@echo "  make build-tier1                    Build the Stage-2 sandbox image (tier 1)"
	@echo ""
	@echo "Smoke (no model needed; uses reference solver):"
	@echo "  make smoke-tier1                    Run the reference FSM through Stage 2 + Stage 3."
	@echo "                                      Must produce mean_score ~7000, replay match."
	@echo ""
	@echo "Fixture (Claude in the loop, no GPU):"
	@echo "  make shim ROOT=/tmp/rb-shim PORT=8765"
	@echo "                                      Start the OpenAI-compatible Claude shim."
	@echo "  make claude-fixture-tier1 RUN_ID=<x> SHIM=http://localhost:8765/v1"
	@echo "                                      Run the minimal agent loop against the shim."
	@echo ""
	@echo "Attempt (real model):"
	@echo "  make attempt MODEL=<id> TIER=1 TASK=2048"
	@echo "                                      Run one full attempt for one (model,tier,task)."
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean DAYS=N                   Delete experiment artifacts older than N days."

build-tier1:
	docker build -t $(TIER1_IMAGE) -f Dockerfile.tier1 .

smoke-tier1: build-tier1
	@mkdir -p $(EXPERIMENTS)/smoke-tier1-reference
	@echo "Running reference FSM through Stage 2..."
	docker run --rm \
	  --network=none \
	  --memory=2g --cpus=2 --pids-limit=256 \
	  -v $(LAB_DIR)/tasks/2048/env.py:/env/env_2048.py:ro \
	  -v $(LAB_DIR)/tasks/2048/baselines/reference_fsm.py:/workspace/submission.py:ro \
	  -v $(EXPERIMENTS)/smoke-tier1-reference:/reports \
	  -e REWARD_BENCH_NUM_GAMES=20 \
	  -e REWARD_BENCH_SEED_BASE=1000 \
	  $(TIER1_IMAGE)
	@echo "Result:"
	@cat $(EXPERIMENTS)/smoke-tier1-reference/result.json | python3 -m json.tool | grep -E '"mean_score"|"median_score"|"max_max_tile"'

shim:
	python3 bin/claude_shim.py --root $(ROOT) --port $(PORT)

clean:
	@find $(EXPERIMENTS) -mindepth 1 -maxdepth 1 -type d -mtime +$${DAYS:-0} -print -exec rm -rf {} +
