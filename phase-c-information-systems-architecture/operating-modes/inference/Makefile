CONTAINER := vllm-inference
include $(shell git rev-parse --show-toplevel)/common.mk

# Same model-registry pattern as wiki-compiler — load active model from
# configs/models.yml using INFERENCE_ACTIVE_MODEL_ID. See ADR 0008.
# This mode shares the model-registry but has no compile-pipeline scripts.
COMPOSE := docker compose --env-file $(FORGE_ROOT)/.env --env-file $(FORGE_ROOT)/phase-c-information-systems-architecture/application-architecture/wiki-compiler/.env.active-model

.PHONY: up down load-active-model

load-active-model:
	@bash $(FORGE_ROOT)/phase-c-information-systems-architecture/application-architecture/wiki-compiler/bin/load-active-model.sh

up: load-active-model
	@$(MAKE) -C caddy up
	$(COMPOSE) up -d

down:
	$(COMPOSE) down 2>/dev/null || true
	@$(MAKE) -C caddy down

.PHONY: smoke
smoke:
	@bash $(FORGE_ROOT)/phase-c-information-systems-architecture/application-architecture/wiki-compiler/tests/smoke.sh
