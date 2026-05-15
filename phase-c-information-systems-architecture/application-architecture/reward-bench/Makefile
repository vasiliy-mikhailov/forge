# reward-bench/Makefile — agentic comprehensiveness benchmark.
# Per ADR 0029 + SPEC.md.
#
# Cycle 93: target names aligned to SPEC.md §Make targets. Implementation
# extras (smoke-tier1, shim, claude-fixture-tier1) kept alongside as
# operational aids. `reward-battery` deferred to cycle 94 (needs
# models.yml iteration logic).

include $(shell git rev-parse --show-toplevel)/common.mk

# Per-tier image tag — bumped per ADR amendment.
# 0.2 — REWARD_BENCH_WALLTIME_BUDGET_SEC=300 (5-min play-time cap, 2026-05-04).
# 0.3 — replace 5-min wall cap with per-game stagnation detector (2026-05-05):
#       REWARD_BENCH_STAGNATION_SEC=60 — if score+max-tile flat for 60s,
#       the game ends as final_state="stagnated". Outer wall cap retained as
#       optional REWARD_BENCH_HARD_WALL_SEC (default 0 = disabled).
TIER1_IMAGE := reward-bench-tier1:0.3
LAB_DIR     := $(shell pwd)
# Resolve $STORAGE_ROOT from forge/.env so EXPERIMENTS lands on /mnt/steam.
STORAGE_ROOT := $(shell grep -E '^STORAGE_ROOT=' $(FORGE_ROOT)/.env | cut -d= -f2)
EXPERIMENTS := $(STORAGE_ROOT)/labs/reward-bench/experiments

# Per-game stagnation budget — score+max-tile must change within this many
# seconds or the game aborts with final_state="stagnated". Override on the
# make line: `make smoke-tier1 STAGNATION_SEC=120`.
STAGNATION_SEC ?= 60

# CLI defaults for `make reward-bench`.
TIER ?= 1
TASK ?= 2048

.PHONY: help \
        reward-bench reward-battery reward-bench-build reward-bench-down reward-bench-clean \
        smoke-tier1 shim claude-fixture-tier1

help:
	@echo "reward-bench — agentic comprehensiveness benchmark"
	@echo ""
	@echo "SPEC.md §Make targets:"
	@echo "  make reward-bench MODEL=<id> [TIER=1] [TASK=2048]"
	@echo "                                      Run one attempt for one (model,tier,task) cell."
	@echo "  make reward-battery TIER=<N> [FILTER=<regex>] [TASK=2048]"
	@echo "                                      Iterate reward-bench over models.yml (cycle 94)."
	@echo "  make reward-bench-build             Build the per-tier sandbox image (tier 1 today)."
	@echo "  make reward-bench-down              No-op; included for symmetry with other labs."
	@echo "  make reward-bench-clean DAYS=N      Delete experiment artifacts older than N days."
	@echo ""
	@echo "Implementation extras (not in SPEC.md):"
	@echo "  make smoke-tier1                    Run the reference FSM through Stage 2 + Stage 3."
	@echo "                                      Must produce mean_score ~7000, replay match."
	@echo "                                      Useful for CI/regression — no LLM needed."
	@echo "  make shim ROOT=/tmp/rb-shim PORT=8765"
	@echo "                                      Start the OpenAI-compatible Claude shim."
	@echo "  make claude-fixture-tier1 RUN_ID=<x> SHIM=http://localhost:8765/v1"
	@echo "                                      Run the minimal agent loop against the shim."

# ---- SPEC.md §Make targets ----

reward-bench:
	@if [ -z "$(MODEL)" ]; then \
	  echo "error: MODEL=<id> required. e.g. make reward-bench MODEL=qwen3.6-27b-awq" >&2; \
	  exit 2; \
	fi
	@echo "[reward-bench] MODEL=$(MODEL) TIER=$(TIER) TASK=$(TASK)"
	python3 -c "from src.reward_bench.frameworks.main import main; \
	            result = main(model_id='$(MODEL)'); \
	            print(result)"

reward-battery:
	@if [ -z "$(TIER)" ]; then \
	  echo "error: TIER=<n> required for reward-battery" >&2; exit 2; \
	fi
	@echo "[reward-battery] TIER=$(TIER) TASK=$(TASK) FILTER=$(FILTER)"
	python3 -m src.reward_bench.frameworks.run_battery \
	  --tier $(TIER) --task $(TASK) \
	  $(if $(FILTER),--filter $(FILTER),)

reward-bench-build:
	docker build -t $(TIER1_IMAGE) -f Dockerfile.tier1 .
	@echo "[reward-bench-build] tier 1 image $(TIER1_IMAGE) built."
	@echo "  TIERS 2-4 deferred: per SPEC.md tier 2-4 are queued backlog."

reward-bench-down:
	@# Per SPEC.md: no-op (no long-running containers); included for
	@# symmetry. We tear down stragglers if any exist.
	@docker ps --filter "name=reward-bench-tier" -q | xargs -r docker stop
	@echo "[reward-bench-down] ok (no long-running containers expected)."

reward-bench-clean:
	@find $(EXPERIMENTS) -mindepth 1 -maxdepth 1 -type d -mtime +$${DAYS:-0} -print -exec rm -rf {} +

# ---- Implementation extras ----

smoke-tier1: reward-bench-build
	@mkdir -p $(EXPERIMENTS)/smoke-tier1-reference
	@echo "Running reference FSM through Stage 2 (stagnation=$(STAGNATION_SEC)s)..."
	docker run --rm \
	  --network=none \
	  --memory=2g --cpus=2 --pids-limit=256 \
	  -v $(LAB_DIR)/tasks/2048/env.py:/env/env_2048.py:ro \
	  -v $(LAB_DIR)/tasks/2048/baselines/reference_fsm.py:/workspace/submission.py:ro \
	  -v $(EXPERIMENTS)/smoke-tier1-reference:/reports \
	  -e REWARD_BENCH_NUM_GAMES=20 \
	  -e REWARD_BENCH_SEED_BASE=1000 \
	  -e REWARD_BENCH_STAGNATION_SEC=$(STAGNATION_SEC) \
	  $(TIER1_IMAGE)
	@echo "Result:"
	@cat $(EXPERIMENTS)/smoke-tier1-reference/result.json | python3 -m json.tool | grep -E '"mean_score"|"median_score"|"max_max_tile"|"stagnation_sec"|"stagnated_any"|"walltime_exceeded"|"aggregate_walltime_sec"'

shim:
	python3 bin/claude_shim.py --root $(ROOT) --port $(PORT)

claude-fixture-tier1:
	@if [ -z "$(RUN_ID)" ] || [ -z "$(SHIM)" ]; then \
	  echo "error: RUN_ID=<x> SHIM=<base-url> required" >&2; \
	  exit 2; \
	fi
	@echo "[claude-fixture-tier1] RUN_ID=$(RUN_ID) SHIM=$(SHIM)"
	@echo "  TODO: agent-loop fixture entry-point. Tracked alongside reward-battery (cycle 94)."
	@exit 1

# ---- Deprecated aliases (cycle 93 transitional; remove in a later cycle) ----

.PHONY: build-tier1 attempt clean
build-tier1: reward-bench-build
	@echo "[deprecated] use 'reward-bench-build' (cycle 93)."

attempt: reward-bench
	@echo "[deprecated] use 'reward-bench' (cycle 93)."

clean: reward-bench-clean
	@echo "[deprecated] use 'reward-bench-clean' (cycle 93)."
