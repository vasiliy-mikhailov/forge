CONTAINER := vllm-inference
include ../../common.mk

# Override up/down to also handle the lab's caddy.
.PHONY: up down

up:
	@$(MAKE) -C caddy up
	$(COMPOSE) up -d

down:
	$(COMPOSE) down
	@$(MAKE) -C caddy down
