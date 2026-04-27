CONTAINER := vllm-inference
include $(shell git rev-parse --show-toplevel)/common.mk

# Override COMPOSE: stack two --env-file's. Order matters — last wins on
# duplicate keys. .env.active-model is rendered by load-active-model.sh
# from configs/models.yml using forge/.env: INFERENCE_ACTIVE_MODEL_ID.
# See ADR 0008.
COMPOSE := docker compose --env-file $(FORGE_ROOT)/.env --env-file .env.active-model

# Override up/down to also handle the lab's caddy + load-active-model step.
.PHONY: up down load-active-model

load-active-model:
	@bash bin/load-active-model.sh

up: load-active-model
	@$(MAKE) -C caddy up
	$(COMPOSE) up -d

down:
	$(COMPOSE) down 2>/dev/null || true
	@$(MAKE) -C caddy down

.PHONY: smoke
smoke:
	@bash tests/smoke.sh
