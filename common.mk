ENVFILE := --env-file $(abspath ../.env)
COMPOSE := docker compose $(ENVFILE)

.PHONY: up down logs build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	docker logs -f $(CONTAINER)

build:
	$(COMPOSE) build
