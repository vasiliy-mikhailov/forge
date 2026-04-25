CONTAINER := jupyter-rl-2048
include ../../common.mk

.PHONY: up down

up:
	@$(MAKE) -C mlflow up
	@$(MAKE) -C caddy up
	$(COMPOSE) up -d

down:
	$(COMPOSE) down
	@$(MAKE) -C caddy down
	@$(MAKE) -C mlflow down
