# Smoke — wiki-compiler

Source of truth for [`./smoke.sh`](smoke.sh). Helper functions
(`pass`/`fail`/`check_*`) come from the shared library
[`../../../../scripts/smoke-lib.sh`](../../../../scripts/smoke-lib.sh).

## Preconditions

- Lab is up: `make wiki-compiler` finished and `vllm-inference`
  reports healthy (this can take 5–10 minutes — model load + warmup +
  CUDA graph capture).
- `forge/.env` has `INFERENCE_DOMAIN`, `VLLM_API_KEY`,
  `INFERENCE_SERVED_NAME`, `INFERENCE_GPU_UUID`.

## Section 1 — containers up

### container up: vllm-inference (healthy)

**Goal.** vLLM Docker container is running and the engine has finished
warm-up (compose healthcheck passing).

**Signals.**
- `docker ps --format '{{.Names}}\t{{.Status}}'` has a row whose name
  is exactly `vllm-inference` and whose status starts with `Up` and
  contains `(healthy)`.

**Edge cases.**
- During cold start the container reports `(health: starting)` for up
  to 10 minutes (compose `start_period: 600s`). Treat this as a fail
  — re-run smoke after warmup.

### container up: kurpatov-wiki-compiler-caddy

**Goal.** Per-lab caddy that fronts `$INFERENCE_DOMAIN` is bound on
:80/:443 and forwarding to `vllm-inference:8000` over `proxy-net`.

**Signals.** Same shape, no healthcheck required (caddy reverse-proxy
has no embedded healthcheck).

## Section 2 — GPU partitioning

### vllm-inference pinned to INFERENCE_GPU_UUID

**Goal.** vLLM sees only the GPU declared in `.env`. Nothing leaks
from the sibling rl-2048 GPU.

**Signals.**
- `docker exec vllm-inference nvidia-smi --query-gpu=uuid --format=csv,noheader`
  whitespace-stripped equals `$INFERENCE_GPU_UUID`.

**Edge cases.**
- Multi-GPU TP (factor=2 or more) would return multiple UUIDs. The
  current single-line comparison would silently match the first.
  When dual-GPU TP arrives, tighten this assertion to "exactly N UUIDs
  match the configured set."

## Section 3 — inference endpoint live

### vLLM serves $INFERENCE_SERVED_NAME via caddy

**Goal.** caddy → vllm-inference → engine → loaded model. Proves
three things at once: caddy reaches the backend, vLLM accepts the API
key, the model loaded successfully.

**Signals.**
- `curl -fsS -H "Authorization: Bearer $VLLM_API_KEY"
  https://$INFERENCE_DOMAIN/v1/models` returns 2xx.
- The JSON's `data[].id` includes `$INFERENCE_SERVED_NAME`.

**Edge cases.**
- Wrong API key → 401. Don't retry — the failure is diagnostic of
  the secret, not vLLM.
- Model still loading → response `{"object":"list","data":[]}` even
  on 200. We catch this by asserting the served name is present.
- Drift between `--served-model-name` flag and `INFERENCE_SERVED_NAME`
  env: 200, but `data[].id` differs. Surface the actual id in the
  failure message.
- This check does **not** issue a chat completion. Token-generation
  surface (sampler, parser, KV cache) is exercised by the bench lab,
  not here.

## Known gaps

- We don't yet measure latency or TPS in smoke. Heavy KV-cache
  fragmentation can degrade throughput silently — adding a small
  `chat/completions` probe with a wall-clock budget is on the list.
- Compose health-check itself only probes `/v1/models`; if vLLM ever
  starts returning a stale model list while the engine is wedged,
  smoke would still pass. Adding a real prompt round-trip would close
  that gap.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
motivation chain inherited from the lab's AGENTS.md.
