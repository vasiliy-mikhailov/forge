.PHONY: up down logs

up:
	docker compose --env-file $(shell git rev-parse --show-toplevel)/.env up -d

down:
	docker compose --env-file $(shell git rev-parse --show-toplevel)/.env down 2>/dev/null || true

logs:
	docker compose logs -f
