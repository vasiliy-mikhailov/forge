# forge — root Makefile. Dispatches into:
#   - phase-c-information-systems-architecture/application-architecture/<lab>/  (labs)
#   - phase-c-information-systems-architecture/operating-modes/<mode>/          (non-lab modes)
#
# Each lab is fully self-contained: own caddy, own docker-compose,
# own SPEC. A non-lab mode (e.g., `inference`) is a lighter operating
# capability that reuses architecture layers without owning a full
# lab structure — see phase-c-…/operating-modes/README.md for the
# mode-vs-lab distinction. All labs and modes are mutually exclusive
# on host ports 80/443 (each binds them via own caddy) and on the
# Blackwell GPU when one of them takes it.
#
# See docs/adr/0007-labs-restructure-self-contained-caddy.md and
# phase-preliminary/adr/0028-inference-mode.md for rationale.

-include .env
export

STORAGE_ROOT ?= /mnt/steam/forge
LABS  := wiki-compiler wiki-ingest wiki-bench rl-2048
MODES := inference

.PHONY: help setup network stop-all ps gpu du smoke push-sources $(LABS) $(MODES)

help:
	@echo "forge — labs + modes orchestrator"
	@echo ""
	@echo "First run:    make setup && make network"
	@echo ""
	@echo "Labs:         $(LABS)"
	@echo "Modes:        $(MODES)"
	@echo "Per target:   make <name>  /  <name>-down  /  <name>-logs  /  <name>-build"
	@echo "Composite:    make stop-all  — stop every lab + mode"
	@echo ""
	@echo "Diagnostics:  make ps / gpu / du / smoke"
	@echo "Content:      make push-sources — move media from ~/Downloads/Курпатов/"
	@echo ""
	@echo "Mutex discipline:"
	@echo "  - Only one mode/lab at a time can hold ports 80/443 (own caddy)."
	@echo "  - wiki-compiler / inference / rl-2048 are mutex on the Blackwell GPU."
	@echo "  - wiki-bench is a client lab — co-runs with wiki-compiler or inference."

setup:
	@: "$${STORAGE_ROOT:?STORAGE_ROOT must be set in .env}"
	@mkdir -p $(STORAGE_ROOT)/shared/models
	@mkdir -p $(STORAGE_ROOT)/labs/wiki-compiler/{caddy-data,caddy-config}
	@mkdir -p $(STORAGE_ROOT)/labs/wiki-ingest/{sources,vault/raw,checkpoints,caddy-data,caddy-config}
	@mkdir -p $(STORAGE_ROOT)/labs/wiki-bench/experiments
	@mkdir -p $(STORAGE_ROOT)/labs/rl-2048/{checkpoints,mlruns,caddy-data,caddy-config}
	@mkdir -p $(STORAGE_ROOT)/labs/inference-mode/{caddy-data,caddy-config}
	@echo "ready: $(STORAGE_ROOT)/{shared,labs}/"

network:
	@docker network inspect proxy-net >/dev/null 2>&1 || docker network create proxy-net

# make <lab>           → bring up
$(LABS): network
	@$(MAKE) -C phase-c-information-systems-architecture/application-architecture/$@ up

# make <mode>          → bring up (non-lab operating modes)
$(MODES): network
	@$(MAKE) -C phase-c-information-systems-architecture/operating-modes/$@ up

# Pattern rules: make <name>-{down,logs,build}.
# Two-tier dispatch: labs live under application-architecture/, modes
# under operating-modes/.
%-down:
	@if [ -d phase-c-information-systems-architecture/application-architecture/$* ]; then \
	  $(MAKE) -C phase-c-information-systems-architecture/application-architecture/$* down; \
	else \
	  $(MAKE) -C phase-c-information-systems-architecture/operating-modes/$* down; \
	fi
%-logs:
	@if [ -d phase-c-information-systems-architecture/application-architecture/$* ]; then \
	  $(MAKE) -C phase-c-information-systems-architecture/application-architecture/$* logs; \
	else \
	  $(MAKE) -C phase-c-information-systems-architecture/operating-modes/$* logs; \
	fi
%-build:
	@if [ -d phase-c-information-systems-architecture/application-architecture/$* ]; then \
	  $(MAKE) -C phase-c-information-systems-architecture/application-architecture/$* build; \
	else \
	  $(MAKE) -C phase-c-information-systems-architecture/operating-modes/$* build; \
	fi

stop-all:
	@for lab  in $(LABS);  do $(MAKE) -C phase-c-information-systems-architecture/application-architecture/$$lab  down 2>/dev/null || true; done
	@for mode in $(MODES); do $(MAKE) -C phase-c-information-systems-architecture/operating-modes/$$mode      down 2>/dev/null || true; done

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
