CONTAINER := jupyter-kurpatov-wiki
include $(shell git rev-parse --show-toplevel)/common.mk

.PHONY: up down

up:
	@$(MAKE) -C caddy up
	$(COMPOSE) up -d

down:
	$(COMPOSE) down
	@$(MAKE) -C caddy down

.PHONY: smoke
smoke:
	@bash tests/smoke.sh
