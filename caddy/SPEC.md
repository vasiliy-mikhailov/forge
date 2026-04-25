# caddy — edge proxy for forge

## Purpose
Single entry point for every public service in forge. Responsibilities:

1. Automatically issue and renew TLS certificates via Let's Encrypt (ACME).
2. Gate access with basic auth — the public-facing services (Jupyter,
   MLflow) either have weak auth of their own or none at all.
3. Route requests to the right container by hostname.

## Non-goals
- Does not do OAuth / SSO / OIDC — basic auth only.
- Does not load-balance across multiple instances — we have one physical
  machine.
- Does not serve static assets.

## Architecture
A `caddy:2` container, bound to `:80` / `:443` on the host. It sits on the
docker network `proxy-net` alongside every other service; container DNS
names (e.g. `jupyter-kurpatov-wiki`, `mlflow`) resolve inside that network,
so the Caddyfile uses `reverse_proxy jupyter-kurpatov-wiki:8888` without
IPs.

All environment-dependent values (domains, user, password hash) are
substituted from the root `.env` — docker compose exposes them as
environment variables, and the Caddyfile reads them via `{$VAR}`.

Volumes:
- `./Caddyfile → /etc/caddy/Caddyfile:ro` — the config, edited in the repo.
- `caddy_data`, `caddy_config` — named volumes, holding certificates and
  runtime state. They survive container recreation; losing them means
  another cycle of ACME certificate issuance, which can hit rate limits.

## Data contracts
Input environment variables:
- `ACME_EMAIL` — required, used as the LE contact.
- `BASIC_AUTH_USER`, `BASIC_AUTH_HASH` — shared across every site block;
  hash is bcrypt.
- `JUPYTER_RL_2048_DOMAIN`, `JUPYTER_KURPATOV_WIKI_DOMAIN`, `MLFLOW_DOMAIN`,
  `INFERENCE_DOMAIN` — full FQDNs.

## Invariants
1. The `proxy-net` network must exist **before** caddy starts (it's created
   by `make network` in the root Makefile).
2. DNS A/AAAA records for every domain point at this host's public IP —
   otherwise the ACME challenge fails.
3. Ports 80/443 on the host are free.
4. All backends join `proxy-net` and listen on `:8888` (jupyter) or `:5000`
   (mlflow), matching the Caddyfile.

## Auth exception: inference
The `INFERENCE_DOMAIN` site block does **not** carry caddy basic auth.
vLLM serves an OpenAI-compatible API where clients send
`Authorization: Bearer <api-key>`; stacking caddy basic auth on top of
that breaks the standard SDKs. The auth layer for that site is vLLM's
own `--api-key`. TLS still terminates at caddy. See
`../inference/docs/adr/0001-vllm-public-openai-compatible-endpoint.md`.

## Status
Production. Stable. Only changes when a new service is added (one site
block + one domain variable in `.env`).

## Open questions
- Do we want OIDC/SSO instead of basic auth? Not for now: one user, basic
  auth is enough.
- Do we want request logging in mlflow/backend for traffic analytics? Not
  now.
