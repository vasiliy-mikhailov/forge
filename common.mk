ENVFILE := --env-file $(abspath ../.env)
COMPOSE := docker compose $(ENVFILE)

# Build all images inside a dedicated buildx builder pinned to CPU 0,
# so cold builds don't starve ssh / mlflow / arbitrage on the host.
# The builder is auto-created on first `make *-build` (see ensure-builder).
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

# Idempotent: create the pinned-core buildx builder if it is missing.
# Every `build` target depends on this; after first run, subsequent
# invocations just short-circuit on the `docker buildx inspect` check.
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
