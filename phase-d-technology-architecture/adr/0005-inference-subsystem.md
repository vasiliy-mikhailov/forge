# ADR 0005 — inference subsystem (vLLM on Blackwell)

## Status
Accepted (2026-04-25). **Subsystem became lab `phase-c-information-systems-architecture/application-architecture/wiki-compiler/` later the same day (ADR 0007).** All design decisions in this ADR carry over verbatim; only the directory layout changed.

## Context
forge needs a long-running inference endpoint that external agents
(Hermes runs, Cowork sessions, custom benchmark harnesses) can call to
drive open-weight models without third-party providers. Up to now we've
used OpenRouter; the failure modes have been infrastructural (free-tier
API errors, rate limits, retry storms inside multi-hour benchmark
runs), not model-quality ones. Meanwhile the Blackwell RTX PRO 6000
96 GB is idle whenever we're not in an active rl-2048 session.

A self-hosted endpoint also unlocks reproducible benchmarking across
open-weight models — the `kurpatov-wiki/skills/benchmark` skill needs
a stable target it can rerun against different model weights without
the API tier muddying the trace.

## Decision
Add a fifth forge subsystem: `inference/`. Single vLLM container,
GPU-pinned to the Blackwell, exposing an OpenAI-compatible HTTP API
at `https://${INFERENCE_DOMAIN}/v1/...` fronted by caddy.

Three cross-cutting design choices captured here; the
**implementation-level** sub-decisions (vLLM vs alternatives, NGC
image vs upstream, vLLM API key vs caddy basic auth) live in
[`phase-c-information-systems-architecture/application-architecture/wiki-compiler/docs/adr/0001`](../../phase-c-information-systems-architecture/application-architecture/wiki-compiler/docs/adr/0001-vllm-public-openai-compatible-endpoint.md).

### 1. Mode mutex with rl-2048
`inference` and `rl-2048` both want the Blackwell. forge has effectively
**two GPU modes for now**: inference mode (`inference` up, `rl-2048`
down) and 2048 mode (`rl-2048` up, `inference` down). The mutex is
not enforced in code — `make stop-all` already exists for exactly
this kind of mode switch and is now extended to also stop `inference`.
Operator manages the swap.

This keeps the door open to future GPU rotation policies (a third
service entering the rotation, automated mode-pinning per cron) without
committing to one now. ADR-able if a third service joins; not yet.

### 2. Auth exception: vLLM API key, no caddy basic auth
caddy fronts every other forge service with shared basic auth
(`BASIC_AUTH_USER` + `BASIC_AUTH_HASH`). We **do not** apply caddy
basic auth to `${INFERENCE_DOMAIN}`. OpenAI-compatible clients send
`Authorization: Bearer …`; stacking caddy basic auth on top breaks
every standard SDK. vLLM has its own `--api-key` enforcement
identical in threat model (one shared secret in `.env`, one operator).
TLS still terminates at caddy.

This is a **documented exception**, not a new pattern: any future
user-facing UI (a Jupyter, a dashboard) goes back to caddy basic auth.

### 3. Shared HF cache via `${STORAGE_ROOT}/shared/models`
Inference reuses the same HuggingFace cache mount that `rl-2048` and
`kurpatov-wiki` already share at `${STORAGE_ROOT}/shared/models →
/root/.cache/huggingface`. Weights downloaded once for inference are
reusable by the GRPO sandbox the next time we swap to 2048 mode. No
new `${STORAGE_ROOT}` subdir.

## Consequences

**Positive.**
- Self-hosted inference at full Blackwell throughput, no third-party.
- Reproducible benchmark target — same skill, same hardware, swap
  models in `.env`.
- Zero additional disk-layout sprawl (HF cache is shared).
- Reversible: removing the subsystem is `make kurpatov-wiki-compiler-down` plus
  deleting `inference/`. Nothing else depends on it (caddy gracefully
  fails the site block if the upstream is down — diagnostic, not
  destructive).

**Negative / accepted.**
- One more docker container to keep healthy + one more domain to
  renew certs for.
- Mode mutex means we can't run a GRPO experiment and serve the
  benchmark endpoint simultaneously. For our usage pattern this is
  fine: experiments are bursts, benchmarks are scheduled.
- API key is a single shared secret; rotation is an `.env` edit +
  `make kurpatov-wiki-compiler-down && make wiki-compiler`.

## Touched files
- New: `inference/{SPEC.md,docker-compose.yml,Makefile,docs/adr/0001-…}`.
- Edits: `caddy/Caddyfile`, `caddy/docker-compose.yml`, `caddy/SPEC.md`,
  `.env.example`, `Makefile` (root), `CLAUDE.md`, `README.md`,
  `tests/smoke.md`, `scripts/smoke.sh`.

## Alternatives rejected
- **Stay on OpenRouter (paid tier).** Buys reliability, doesn't use the
  Blackwell, doesn't give us reproducible local benchmarking against
  whatever-model-we-want.
- **Move rl-2048 permanently to RTX 5090.** Constrains future GRPO
  experiments to 32 GB; not worth the tradeoff. The mutex is cheap.
- **Add caddy basic auth on top of vLLM API key.** Breaks OpenAI SDKs
  for ergonomics no one wants. Rejected.
