# ADR 0001 — vLLM as a public OpenAI-compatible endpoint

## Status
Accepted (2026-04-25).

## Context
forge needs a long-running inference endpoint that external agents
(Hermes, Cowork, custom benchmark harnesses) can call to drive
open-weight models. Up to now we've used third-party providers
(OpenRouter free tier), and the failure modes are infrastructural —
free-tier API errors, rate limits, retry storms — not model-quality
ones. We have a Blackwell RTX PRO 6000 96 GB sitting idle when rl-2048
is not running. Use it.

## Decision
Add a new forge subsystem `inference/` that runs **vLLM in a single
docker container**, GPU-pinned to the Blackwell, exposing an
**OpenAI-compatible HTTP API** at `https://${INFERENCE_DOMAIN}/v1/...`.

Three sub-decisions inside this:

### 1. vLLM, not TGI / TensorRT-LLM / SGLang
vLLM has the broadest open-weight model coverage, the fastest moving
quantization story (AWQ + Marlin + TurboQuant KV cache all production
in 2026), an OpenAI-compatible server out of the box, and the cleanest
Blackwell SM120 path through NVIDIA's NGC container as of the March
2026 release. Alternatives:
- **TensorRT-LLM**: faster on Blackwell-native FP4 but requires per-model
  engine builds and the model-zoo coverage lags vLLM by months.
- **SGLang**: comparable to vLLM, smaller community, no clear advantage
  for this workload.
- **TGI (HF)**: lags on quantization features, smaller community than
  vLLM in 2026.
Reversibility: low cost — swapping serving framework is one subsystem
edit, not a forge-wide change.

### 2. Docker Hub stable vLLM, not NGC
First pass at this ADR favored `nvcr.io/nvidia/vllm` (NGC) on the
assumption that NGC was the canonical Blackwell-friendly distribution.
At deploy time (2026-04-25) the specific tag `25.03-py3` was unreachable
(`manifest unknown`). Switched to Docker Hub
`vllm/vllm-openai:v0.19.1-cu130-ubuntu2404` (released 2026-04-20), which
works first-try on SM120 with the same host's `nvidia-driver-590-open`
(CUDA 13.1 reported by `nvidia-smi`). Docker Hub vLLM has caught up to
NGC for Blackwell support during 2026; the historical lag through
late 2025 no longer applies. Reversibility: high — one image tag swap.

Also swapped `--kv-cache-dtype turboquant_4bit_nc` → `fp8` at deploy:
TurboQuant lives only in vLLM nightlies as of v0.19.1 stable; FP8 KV
cache is the documented stable fallback the SPEC already mentioned.
Will upgrade when TurboQuant ships in a stable release.

### 3. vLLM API-key auth, no caddy basic auth
caddy fronts every other forge service with shared basic auth
(`BASIC_AUTH_USER` + `BASIC_AUTH_HASH`). We **do not** use basic auth on
`${INFERENCE_DOMAIN}`. Reasoning:
- OpenAI-compatible clients send `Authorization: Bearer …`. Stacking
  `Authorization: Basic …` underneath breaks every standard SDK
  (langchain, openai-python, litellm, the Hermes harness).
- vLLM has its own per-server `--api-key` enforcement, identical
  threat model to the basic auth used elsewhere (one shared secret in
  `.env`, one operator).
- TLS termination still happens at caddy.
This is a documented **exception** to the forge auth pattern, not a
new pattern: any future user-facing UI (a Jupyter, a dashboard) goes
back to basic auth via caddy as before.

## Consequences

**Positive.**
- forge gains a self-hosted inference endpoint usable from anywhere on
  the internet with `Authorization: Bearer …`, no third-party.
- The shared `${STORAGE_ROOT}/models` HF cache means weights downloaded
  for inference are also reusable by `rl-2048` and `kurpatov-wiki`.
- Reversible: removing the subsystem is `make inference-down` plus
  deleting the folder; nothing else depends on it.

**Negative / accepted constraints.**
- Mutex with `rl-2048` on the Blackwell. forge has effectively two
  modes: inference and 2048. Not enforced in code; documented in
  `inference/SPEC.md` and `CLAUDE.md`. Operator manages the swap via
  `make stop-gpu` between modes.
- Ops surface grows: one more container to keep healthy, one more
  domain to renew certs for.
- API key is a single shared secret. If it leaks, rotate via `.env`
  edit + `make inference-down && make inference`.

## Alternatives rejected
- **NGC `nvcr.io/nvidia/vllm:25.03-py3`.** Tag did not exist at deploy.
  Docker Hub stable was strictly the right call.
- **Use OpenRouter paid tier instead.** Solves the reliability issue but
  not the "use the Blackwell that's already paid for" point. Also locks
  benchmarks to whatever models OpenRouter happens to host.
- **Multi-GPU tensor-parallel across Blackwell + RTX 5090.** No NVLink;
  PCIe-only TP for 70B models is slower than single-card. RTX 5090 is
  better used for `kurpatov-wiki` (its current assignment) or kept idle.
- **Stack basic auth on top of API key.** Breaks OpenAI SDKs; rejected
  for ergonomics.
