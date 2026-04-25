CONTAINER := jupyter-kurpatov-wiki
include ../../common.mk

.PHONY: up down

up:
	@$(MAKE) -C caddy up
	$(COMPOSE) up -d

down:
	$(COMPOSE) down
	@$(MAKE) -C caddy down
