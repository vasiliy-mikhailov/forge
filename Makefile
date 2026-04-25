# forge — root Makefile. Disp atches into labs/<lab>/.
#
# Each lab is fully self-contained: own caddy, own docker-compose,
# own SPEC. Labs are mutually exclusive on host ports 80/443
# (each lab's caddy binds them); they're also mutex on the
# Blackwell GPU when one lab takes both cards via dual-GPU TP.
#
# See docs/adr/0007-labs-restructure-self-contained-caddy.md for
# rationale.

-include .env
export

STORAGE_ROOT ?= /mnt/steam/forge
LABS := kurpatov-wiki-compiler kurpatov-wiki-ingest kurpatov-wiki-bench rl-2048

.PHONY: help setup network stop-all ps gpu du smoke push-sources $(LABS)

help:
	@echo "forge — labs orchestrator"
	@echo ""
	@echo "First run:    make setup && make network"
	@echo ""
	@echo "Labs:         $(LABS)"
	@echo "Per lab:      make <lab>  /  <lab>-down  /  <lab>-logs  /  <lab>-build"
	@echo "Composite:    make stop-all  — stop every lab"
	@echo ""
	@echo "Diagnostics:  make ps / gpu / du / smoke"
	@echo "Content:      make push-sources — move media from ~/Downloads/Курпатов/"
	@echo ""
	@echo "Lab discipline (mutex):"
	@echo "  - Only one lab at a time can hold ports 80/443 (own caddy)."
	@echo "  - kurpatov-wiki-compiler can co-run with kurpatov-wiki-bench"
	@echo "    (bench is a client, no caddy)."
	@echo "  - Going to dual-GPU TP for compiler also locks both GPUs."

setup:
	@: "$${STORAGE_ROOT:?STORAGE_ROOT must be set in .env}"
	@mkdir -p $(STORAGE_ROOT)/shared/models
	@mkdir -p $(STORAGE_ROOT)/labs/kurpatov-wiki-compiler/{caddy-data,caddy-config}
	@mkdir -p $(STORAGE_ROOT)/labs/kurpatov-wiki-ingest/{sources,vault/raw,checkpoints,caddy-data,caddy-config}
	@mkdir -p $(STORAGE_ROOT)/labs/kurpatov-wiki-bench/experiments
	@mkdir -p $(STORAGE_ROOT)/labs/rl-2048/{checkpoints,mlruns,caddy-data,caddy-config}
	@echo "ready: $(STORAGE_ROOT)/{shared,labs}/"

network:
	@docker network inspect proxy-net >/dev/null 2>&1 || docker network create proxy-net

# make <lab>           → bring up
$(LABS): network
	@$(MAKE) -C labs/$@ up

# Pattern rules: make <lab>-{down,logs,build}.
%-down:
	@$(MAKE) -C labs/$* down
%-logs:
	@$(MAKE) -C labs/$* logs
%-build:
	@$(MAKE) -C labs/$* build

stop-all:
	@for lab in $(LABS); do $(MAKE) -C labs/$$lab down 2>/dev/null || true; done

ps:
	@docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

gpu:
	@nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv

du:
	@du -sh $(STORAGE_ROOT)/* 2>/dev/null || echo "$(STORAGE_ROOT) is empty"

smoke:
	@bash scripts/smoke.sh

push-sources:
	@bash scripts/push-sources.sh
