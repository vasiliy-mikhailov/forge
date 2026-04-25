# Bench is a one-shot harness, not a service. It uses Docker but
# doesn't bind ports or join proxy-net, so it co-runs with
# kurpatov-wiki-compiler (the LLM endpoint it talks to).
#
# Targets:
#   make build               — build the OpenHands sandbox image
#   make storage-init        — create $STORAGE_ROOT/labs/kurpatov-wiki-bench/experiments/
#   make bench               — one experiment against the model in .env
#   make preflight           — confirm the compiler lab is up + serving the expected model
#   make clean-experiments   — wipe experiments dir (prompts first)

-include $(shell git rev-parse --show-toplevel)/.env
export

.PHONY: help build bench preflight storage-init clean-experiments up down logs

help:
	@echo "labs/kurpatov-wiki-bench — agent benchmark harness"
	@echo ""
	@echo "  make build               — build the sandbox image"
	@echo "  make storage-init        — create experiments dir"
	@echo "  make bench               — run one experiment"
	@echo "  make preflight           — check compiler lab is up + serving expected model"

storage-init:
	@: "$${STORAGE_ROOT:?STORAGE_ROOT must be set in forge/.env}"
	@mkdir -p $(STORAGE_ROOT)/labs/kurpatov-wiki-bench/experiments
	@echo "ready: $(STORAGE_ROOT)/labs/kurpatov-wiki-bench/experiments/"

build:
	@: "$${OPENHANDS_VERSION:?OPENHANDS_VERSION must be set in .env}"
	@if [ ! -x bin/openhands ]; then \
	  echo "FATAL: bin/openhands missing. See README → 'Install the CLI binary'."; \
	  exit 2; \
	fi
	docker build -t kurpatov-wiki-bench:$(OPENHANDS_VERSION) .
	@docker images kurpatov-wiki-bench --format 'built: {{.Repository}}:{{.Tag}}  size={{.Size}}'

bench: storage-init
	@./run.sh

preflight:
	@: "$${INFERENCE_BASE_URL:?}" "$${VLLM_API_KEY:?}" "$${INFERENCE_SERVED_NAME:?}"
	@served=$$(curl -fsS "$(INFERENCE_BASE_URL)/models" -H "Authorization: Bearer $(VLLM_API_KEY)" | jq -r '.data[0].id'); \
	  if [ "$$served" = "$(INFERENCE_SERVED_NAME)" ]; then \
	    echo "OK — compiler lab serves '$$served'"; \
	  else \
	    echo "MISMATCH — serves '$$served', .env expects '$(INFERENCE_SERVED_NAME)'"; \
	    exit 1; \
	  fi

clean-experiments:
	@: "$${STORAGE_ROOT:?}"
	@read -p "Wipe $(STORAGE_ROOT)/labs/kurpatov-wiki-bench/experiments/ ? [y/N] " ans && [ "$$ans" = "y" ] && rm -rf $(STORAGE_ROOT)/labs/kurpatov-wiki-bench/experiments/* || echo "aborted"

# Compatibility shims so root Makefile's `make kurpatov-wiki-bench` works.
# Bench is "started" by running an experiment; "down" is no-op since it's
# not a long-running service.
up: bench
down:
	@true
logs:
	@echo "(bench is one-shot — see ${STORAGE_ROOT}/labs/kurpatov-wiki-bench/experiments/<id>/events.jsonl)"

.PHONY: smoke
smoke:
	@bash tests/smoke.sh
