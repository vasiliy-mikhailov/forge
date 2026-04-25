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
A single container `vllm-inference`, built from
`vllm/vllm-openai:v0.19.1-cu130-ubuntu2404` (Docker Hub, stable release
from 2026-04-20). Earlier draft of this SPEC referenced an
`nvcr.io/nvidia/vllm` NGC tag that did not exist at deploy time; the
Docker Hub stable image carries Blackwell SM120 paths and is the
working choice. CUDA 13 runtime, requires driver 580+ (we run 590-open
per ADR 0004). GPU passthrough via `INFERENCE_GPU_UUID`, defaulting to
`${GPU_BLACKWELL_UUID}`.

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
  vLLM auto-converts the AWQ checkpoint to AWQ-Marlin runtime kernels
  on load (`The model is convertible to awq_marlin during runtime`).
- **KV cache**: FP8 (`--kv-cache-dtype fp8`). TurboQuant K4V4
  (Hadamard-rotated scalar quantization, ICLR 2026) is the eventual
  target — sub-4-bit-equivalent compression with ~zero quality loss —
  but as of 2026-04 it lives only in vLLM nightlies
  (`turboquant_4bit_nc` errors `invalid choice` on stable v0.19.1).
  FP8 KV cache is half the memory footprint of FP16 with negligible
  accuracy loss for chat workloads; we'll migrate to TurboQuant when
  it lands in a stable vLLM release.
- **Activations**: model-native (FP16). FP4 activations on Blackwell
  are a future option once vLLM exposes a stable W4A4 path; not on by
  default here.

For `cyankiwi/Qwen3.6-27B-AWQ-INT4` (default) at 64K context
(YaRN-extended, see below) this means ~50 GB GPU at load + FP8 KV
cache giving 60 GB pool / ~26× concurrency at full 64K + ~5 GB
CUDA-graph and activation overhead. The model is a multimodal VL
variant we run in text-only mode here; the multimodal path is
dormant unless requests carry images. Quantization auto-detected
(compressed-tensors INT4 → MarlinLinearKernel). Qwen 3.6/Qwen3 had no
official dense 72B-Instruct-AWQ at deploy time; community 72B GGUFs
are not vLLM-loadable, so 32B-AWQ is the apples-to-apples comparison
class for our open-weight benchmark runs.

## Context extension (YaRN)
Default `INFERENCE_MAX_MODEL_LEN=65536` is above Qwen3-32B's native 32K
context window; it's enabled via YaRN rope-scaling, baked into the
compose `command:` as:

```
--hf-overrides.rope_scaling.rope_type yarn
--hf-overrides.rope_scaling.factor 2.0
--hf-overrides.rope_scaling.original_max_position_embeddings 32768
```

64K is the minimum some agent harnesses (e.g. Hermes Agent) accept;
hence the default. To extend further (Qwen3 supports YaRN to 128K with
factor=4.0), edit the `factor` flag and bump `INFERENCE_MAX_MODEL_LEN`.

The dot-notation `--hf-overrides.<key>` form is used over the older
`--rope-scaling '{json}'` flag because vLLM v0.19 dropped the latter,
and because YAML's folded scalar (`>`) form in compose strips JSON
quotes that bare-arg JSON would need.

Caveat: the YaRN parameters above are tuned for the **Qwen3 / Qwen2.5
family** (rope_theta, base context). Other model families (Llama,
Mistral, Gemma) will need different `original_max_position_embeddings`
and possibly different `rope_type`. When swapping models, check the
target model's `config.json` and adjust.

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
  `65536` (YaRN-extended; see `## Context extension (YaRN)` above).
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

## Reasoning models (Qwen3 family)
Qwen3 is a reasoning-tuned line: by default it emits a `<think>...</think>` block before its final answer. For benchmark workloads where exposed CoT is not needed (and where token budgets matter), pass `chat_template_kwargs: {enable_thinking: false}` in the request body. With it on, plan for ~10-20× more completion tokens per response.

## Tool calling and reasoning
Default config enables OpenAI-compatible tool calls plus reasoning
extraction:

```
--enable-auto-tool-choice
--tool-call-parser qwen3_xml
--reasoning-parser qwen3
```

The `qwen3_xml` tool-call parser extracts Qwen3/Qwen3.6 XML-tagged
tool calls (`<tool_call>{...}</tool_call>`) into the OpenAI
`tool_calls[]` field. Earlier setups used the `hermes` parser; that
works for trivial cases but loses fidelity on Qwen3's actual emission
format — the model's reasoning leaks into `content` and complex tool
calls fail to parse. `qwen3_xml` is the right pick for any Qwen3+
family model.

The `qwen3` reasoning parser extracts `<think>...</think>` blocks
into a separate `reasoning` (or `reasoning_content`) field on the
response, leaving `content` clean. Without it, the closing `</think>`
tag and the chain-of-thought leak into `content` and confuse agent
harnesses (e.g. Hermes Agent silently wedges).

With both parsers active, a `tools` request returns:
  `finish_reason: tool_calls`
  `content: null`
  `reasoning: "...the chain of thought..."`
  `tool_calls: [{...properly extracted...}]`
Without `--enable-auto-tool-choice` vLLM returns HTTP 400 to any
request that includes a `tools:[...]` block:
`"auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set`.

Other parser names available in vLLM v0.19
(`--help=tool-call-parser`): `deepseek_v3*`, `gemma4`, `glm45/47`,
`granite*`, `hermes`, `kimi_k2`, `llama3_json`, `llama4_*`,
`minimax*`, `mistral`, `qwen3_coder`, `qwen3_xml`, `pythonic`, …
When swapping models, pick the parser that matches the new model's
emitted tool-call format. Same applies to `--reasoning-parser`:
there are family-specific extractors (qwen3, deepseek_r1, glm45, …)
for models that emit `<think>` blocks.

## Open questions
- Do we ever want a second model loaded simultaneously (e.g. a small
  draft model on RTX 5090 for speculative decoding)? Not now; the RTX
  5090 stays with `kurpatov-wiki` for transcription. Revisit if the
  benchmark workload makes throughput a bottleneck.
- Do we want vLLM's `/metrics` (Prometheus) wired into a future
  observability subsystem? Not now; surface to the operator if the
  question becomes real.
