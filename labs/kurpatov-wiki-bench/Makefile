.PHONY: help build bench preflight clean-runs storage-init

help:
	@echo "kurpatov-wiki-bench — sandboxed agent harness for the wiki authoring benchmark"
	@echo ""
	@echo "  make storage-init      — create \$$STORAGE_ROOT/kurpatov-wiki-bench/runs/"
	@echo "  make build             — build the Docker image (one-time, or after CLI bump)"
	@echo "  make bench             — run one bench against the model in .env (sandboxed)"
	@echo "  make preflight         — confirm vLLM is up + serving the configured model"
	@echo "  make clean-runs        — wipe \$$STORAGE_ROOT/kurpatov-wiki-bench/runs/ (prompts first)"
	@echo ""
	@echo "Override per-invocation:  INFERENCE_SERVED_NAME=qwen3-32b make bench"

# .env is sourced once for help / image tag composition.
-include .env
export

storage-init:
	@: "$${STORAGE_ROOT:?STORAGE_ROOT must be set in .env}"
	@mkdir -p $(STORAGE_ROOT)/kurpatov-wiki-bench/runs
	@echo "ready: $(STORAGE_ROOT)/kurpatov-wiki-bench/runs/"

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
	    echo "OK — vLLM serves '$$served'"; \
	  else \
	    echo "MISMATCH — vLLM serves '$$served', .env expects '$(INFERENCE_SERVED_NAME)'"; \
	    exit 1; \
	  fi

clean-runs:
	@: "$${STORAGE_ROOT:?}"
	@read -p "Wipe $(STORAGE_ROOT)/kurpatov-wiki-bench/runs/ ? [y/N] " ans && [ "$$ans" = "y" ] && rm -rf $(STORAGE_ROOT)/kurpatov-wiki-bench/runs/* || echo "aborted"
