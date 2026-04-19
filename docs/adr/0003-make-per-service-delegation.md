# ADR 0003 — one root Makefile, delegates into subfolders

## Status
Accepted (2026-04-19).

## Context
Every service needs the same operations: `up`, `down`, `logs`, `build`.
Plus I want composite targets: `make base` (caddy + mlflow), `make
stop-gpu` (stop everything using a GPU).

Bad options:

- One giant compose file covering everything — loses isolation, restarting
  one service touches all of them.
- Copy-pasting the Makefile into every subfolder — hard to evolve.
- A CLI wrapper in Python/Go — overkill for ~10 commands.

## Decision
Two-level make layout:

- **Root Makefile** knows the list of services
  `SERVICES := caddy mlflow rl-2048 kurpatov-wiki`, the composite targets,
  `make setup`, and diagnostics. It delegates into subfolders via pattern
  rules:

  ```makefile
  $(SERVICES): network       ; @$(MAKE) -C $@ up
  %-down   ; @$(MAKE) -C $* down
  %-logs   ; @$(MAKE) -C $* logs
  %-build  ; @$(MAKE) -C $* build
  ```

- **Per-service Makefile**: two lines. Include `common.mk` and set
  `CONTAINER := <name>`:

  ```makefile
  CONTAINER := jupyter-kurpatov-wiki
  include ../common.mk
  ```

- **common.mk** implements `up/down/logs/build` via
  `docker compose --env-file ../.env`.

## Consequences
- Plus: one `.env` at the repo root; every service sees the same variables.
- Plus: adding a service = one folder + two lines in a Makefile + one entry
  in `SERVICES`.
- Plus: commands stay short and uniform: `make <service>`,
  `make <service>-down`, `make <service>-logs`, `make <service>-build`.
- Minus: make pattern rules are a bit magical. `make foo` for a
  non-existent service yields a not-very-friendly error.

## Alternatives considered
- **`COMPOSE_FILE`/`COMPOSE_PROJECT_NAME` in one root `.env`** with a single
  compose project — harder to develop services independently.
- **just / task / recursive make include** without a per-service Makefile —
  short, but loses the "I can `cd service/ && make up`" workflow.
