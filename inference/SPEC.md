# inference — public OpenAI-compatible vLLM endpoint

## Purpose
A long-running vLLM container exposing an OpenAI-compatible HTTP API at
`https://${INFERENCE_DOMAIN}/v1/...`, fronted by caddy with auto-LE TLS.
Used by external agents (Hermes, Cowork sessions, custom benchmark
harnesses) to drive open-weight models without depending on third-party
inference providers.

## Non-goals
- Not multi-tenant — one user, one model loaded at a time.
- Not a model-zoo dispatcher — to swap models, edit `.env`,
  `make inference-down`, `make inference`. Hot-swap is out of scope.
- Not load-balanced — one container, one GPU. If saturation becomes a
  problem, we add concurrency knobs in vLLM, not a second container.
- Not multi-GPU — single Blackwell. Tensor-parallel across PCIe is slower
  than single-card inference for 70B-class models with no NVLink.

## Mode mutex with rl-2048
`inference` and `rl-2048` both want the Blackwell. forge has effectively
two modes: **inference mode** (this service running, `rl-2048` stopped)
and **2048 mode** (`rl-2048` running, `inference` stopped). Bringing both
up at once will OOM or fail nvidia-container-toolkit GPU allocation.

Discipline:
```
make stop-gpu      # stops kurpatov-wiki + rl-2048 + inference
make inference     # → inference mode
make rl-2048       # → 2048 mode (you do this only after make inference-down)
```
The Makefile does not enforce the mutex; forge convention is one
operator, the operator manages mode transitions deliberately.

## Architecture
A single container `vllm-inference`, built from `nvcr.io/nvidia/vllm`
(NGC image — has Blackwell SM120 paths landed by the March 2026 release;
upstream `vllm/vllm-openai` lags). GPU passthrough via
`INFERENCE_GPU_UUID`, defaulting to `${GPU_BLACKWELL_UUID}`.

The container speaks OpenAI-compatible HTTP on `:8000` inside the
`proxy-net` docker network. Caddy reverse-proxies `${INFERENCE_DOMAIN}`
to `vllm-inference:8000`. **No basic auth on this site block** — the
authentication layer is vLLM's own `--api-key`, because OpenAI clients
send `Authorization: Bearer …` and stacking caddy basic auth on top of
that breaks every standard SDK. See
`docs/adr/0001-vllm-public-openai-compatible-endpoint.md`.

Volumes:
- `${STORAGE_ROOT}/models → /root/.cache/huggingface` — shared HF cache
  (same volume rl-2048 and kurpatov-wiki use; weights downloaded once,
  used by all three modes).

Quantization stack at default config:
- **Weights**: 4-bit, AWQ via Marlin kernels (`--quantization awq_marlin`).
- **KV cache**: 4-bit, TurboQuant K4V4 (`--kv-cache-dtype turboquant_4bit_nc`).
  Hadamard-rotated scalar quantization, sub-4-bit-equivalent compression
  with ~zero quality loss; ICLR 2026, merged into vLLM late 2025.
- **Activations**: model-native (FP16/BF16). FP4 activations on Blackwell
  are a future option once vLLM exposes a stable W4A4 path; not on by
  default here.

For Qwen3-72B-Instruct-AWQ at 32K context this means ~35 GB weights +
~8 GB compressed KV cache + ~10 GB activations/overhead — comfortably
inside 96 GB with headroom for batched concurrency.

## Data contracts
Input environment variables (all from forge root `.env`):
- `INFERENCE_DOMAIN` — required, FQDN. Caddy serves this.
- `INFERENCE_GPU_UUID` — required, single GPU UUID. Default in
  `.env.example`: `${GPU_BLACKWELL_UUID}`.
- `VLLM_API_KEY` — required. The `Authorization: Bearer …` value. Generate
  with e.g. `openssl rand -hex 32`.
- `INFERENCE_MODEL` — HuggingFace model id, e.g.
  `Qwen/Qwen3-72B-Instruct-AWQ`.
- `INFERENCE_SERVED_NAME` — public model name in the OpenAI API
  (`/v1/models` returns this). Default: `qwen3-72b-instruct`.
- `INFERENCE_MAX_MODEL_LEN` — context window cap in tokens. Default:
  `32768`. Raise once we've measured that KV cache fits at higher length.
- `HF_TOKEN` — optional, only needed if the chosen model is gated.
- `STORAGE_ROOT` — for the HF cache mount.

Output:
- An OpenAI-compatible HTTP endpoint at `https://${INFERENCE_DOMAIN}/v1/`
  (chat/completions, completions, models). Auth: `Authorization: Bearer
  ${VLLM_API_KEY}`.

## Invariants
1. `proxy-net` exists (created by `make network` in root) before
   `make inference`.
2. `${INFERENCE_DOMAIN}` resolves to this host's public IP.
3. `INFERENCE_GPU_UUID` is not held by any other forge container (i.e.
   `rl-2048` is down).
4. `${STORAGE_ROOT}/models` exists (created by `make setup`).
5. Caddy is up before external traffic can reach the endpoint —
   `make base` if not already running.

## Status
New. Smoke-test target lives in `tests/smoke.md` section 9; the script
runs section 9 only when the container is up, otherwise skips
(consistent with forge's "not all services run all the time" pattern).

## Open questions
- Do we ever want a second model loaded simultaneously (e.g. a small
  draft model on RTX 5090 for speculative decoding)? Not now; the RTX
  5090 stays with `kurpatov-wiki` for transcription. Revisit if the
  benchmark workload makes throughput a bottleneck.
- Do we want vLLM's `/metrics` (Prometheus) wired into a future
  observability subsystem? Not now; surface to the operator if the
  question becomes real.
