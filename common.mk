# common.mk — included by each lab's Makefile + sublab Makefiles.
# Discovers forge root via git so it works at any nesting depth
# (labs/<lab>/ or labs/<lab>/<sublab>/).

FORGE_ROOT     := $(shell git rev-parse --show-toplevel)
ENVFILE        := --env-file $(FORGE_ROOT)/.env
COMPOSE        := docker compose $(ENVFILE)

# buildx builder pinned to CPU 0, so cold builds don't starve
# ssh / mlflow / arbitrage on the host. Auto-created on first build.
BUILDER        := slowbuilder
BUILD_CPUSET   := 0
BUILDER_CTR    := buildx_buildkit_$(BUILDER)0

.PHONY: up down logs build ensure-builder

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	docker logs -f $(CONTAINER)

ensure-builder:
	@if ! docker buildx inspect $(BUILDER) >/dev/null 2>&1; then \
	  echo ">>> creating buildx builder '$(BUILDER)' pinned to CPU $(BUILD_CPUSET)"; \
	  docker buildx create --name $(BUILDER) \
	    --driver docker-container \
	    --driver-opt cpuset-cpus=$(BUILD_CPUSET) \
	    --bootstrap >/dev/null; \
	  docker update --restart unless-stopped $(BUILDER_CTR) >/dev/null; \
	fi

build: ensure-builder
	BUILDX_BUILDER=$(BUILDER) $(COMPOSE) build
