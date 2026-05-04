# reward-bench/Makefile — agentic comprehensiveness benchmark.
# Per ADR 0029 + SPEC.md.

include $(shell git rev-parse --show-toplevel)/common.mk

# Per-tier image tag — bumped per ADR amendment.
# 0.2 — adds REWARD_BENCH_WALLTIME_BUDGET_SEC=300 (5-min play-time cap, 2026-05-04).
TIER1_IMAGE := reward-bench-tier1:0.2
LAB_DIR     := $(shell pwd)
# Resolve $STORAGE_ROOT from forge/.env so EXPERIMENTS lands on /mnt/steam.
STORAGE_ROOT := $(shell grep -E '^STORAGE_ROOT=' $(FORGE_ROOT)/.env | cut -d= -f2)
EXPERIMENTS := $(STORAGE_ROOT)/labs/reward-bench/experiments

# Default Stage-2 walltime budget (per attempt, in seconds). Override on the
# make line: `make smoke-tier1 PLAY_BUDGET=600`.
PLAY_BUDGET ?= 300
# Hard outer kill (docker-side belt-and-suspenders) — give the in-container
# guard a small grace period to write result.json before the SIGKILL lands.
DOCKER_TIMEOUT_SEC := $(shell echo $$(($(PLAY_BUDGET) + 60)))

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
	@echo "Running reference FSM through Stage 2 (budget=$(PLAY_BUDGET)s, hard kill=$(DOCKER_TIMEOUT_SEC)s)..."
	timeout --signal=SIGTERM --kill-after=10 $(DOCKER_TIMEOUT_SEC) \
	docker run --rm \
	  --network=none \
	  --memory=2g --cpus=2 --pids-limit=256 \
	  -v $(LAB_DIR)/tasks/2048/env.py:/env/env_2048.py:ro \
	  -v $(LAB_DIR)/tasks/2048/baselines/reference_fsm.py:/workspace/submission.py:ro \
	  -v $(EXPERIMENTS)/smoke-tier1-reference:/reports \
	  -e REWARD_BENCH_NUM_GAMES=20 \
	  -e REWARD_BENCH_SEED_BASE=1000 \
	  -e REWARD_BENCH_WALLTIME_BUDGET_SEC=$(PLAY_BUDGET) \
	  $(TIER1_IMAGE)
	@echo "Result:"
	@cat $(EXPERIMENTS)/smoke-tier1-reference/result.json | python3 -m json.tool | grep -E '"mean_score"|"median_score"|"max_max_tile"|"walltime_budget_sec"|"walltime_exceeded"|"aggregate_walltime_sec"'

shim:
	python3 bin/claude_shim.py --root $(ROOT) --port $(PORT)

clean:
	@find $(EXPERIMENTS) -mindepth 1 -maxdepth 1 -type d -mtime +$${DAYS:-0} -print -exec rm -rf {} +
