# .env holds server-side config (STORAGE_ROOT, domains, GPU UUIDs, secrets).
# Optional so the Makefile also loads on laptop clones where .env doesn't
# exist (needed for laptop-only targets like `push-sources`).
-include .env
export

STORAGE_ROOT ?= /mnt/steam/forge
SERVICES := caddy mlflow rl-2048 kurpatov-wiki

.PHONY: help setup network base base-down stop-gpu ps gpu du smoke push-sources $(SERVICES)

help:
	@echo "First run:     make setup && make base"
	@echo ""
	@echo "Services:      $(SERVICES)"
	@echo "Per service:   make <name>  /  <name>-down  /  <name>-logs  /  <name>-build"
	@echo ""
	@echo "Composite:"
	@echo "  make base       — caddy + mlflow"
	@echo "  make base-down  — stop everything"
	@echo "  make stop-gpu   — stop rl-2048 + kurpatov-wiki"
	@echo ""
	@echo "Content:"
	@echo "  make push-sources — move media from ~/Downloads/Курпатов/ to server over LAN"
	@echo "                      (video + audio; see scripts/push-sources.sh for MODULE override)"
	@echo ""
	@echo "Diagnostics:   make ps / gpu / du / smoke"

setup:
	@mkdir -p $(STORAGE_ROOT)/models
	@mkdir -p $(STORAGE_ROOT)/rl-2048/checkpoints
	@mkdir -p $(STORAGE_ROOT)/kurpatov-wiki/sources
	@mkdir -p $(STORAGE_ROOT)/kurpatov-wiki/checkpoints
	@mkdir -p $(STORAGE_ROOT)/kurpatov-wiki/vault/raw
	@mkdir -p $(STORAGE_ROOT)/mlflow/mlruns
	@mkdir -p mlflow/data rl-2048/notebooks kurpatov-wiki/notebooks

network:
	@docker network inspect proxy-net >/dev/null 2>&1 || docker network create proxy-net

# make <service>           → bring up
$(SERVICES): network
	@$(MAKE) -C $@ up

# make <service>-down      → stop
# make <service>-logs      → logs
# make <service>-build     → rebuild
%-down:
	@$(MAKE) -C $* down
%-logs:
	@$(MAKE) -C $* logs
%-build:
	@$(MAKE) -C $* build

# Composite targets
base: caddy mlflow
base-down:
	@$(MAKE) -C kurpatov-wiki down
	@$(MAKE) -C rl-2048 down
	@$(MAKE) -C mlflow down
	@$(MAKE) -C caddy down
stop-gpu:
	@$(MAKE) -C rl-2048 down
	@$(MAKE) -C kurpatov-wiki down

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
