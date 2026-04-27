# wiki-compiler — public OpenAI-compatible vLLM endpoint

## Purpose
A long-running vLLM container exposing an OpenAI-compatible HTTP API at
`https://${INFERENCE_DOMAIN}/v1/...`, fronted by caddy with auto-LE TLS.
Used by external agents (Hermes, Cowork sessions, custom benchmark
harnesses) to drive open-weight models without depending on third-party
inference providers.

## Non-goals
- Not multi-tenant — one user, one model loaded at a time.
- Not a model-zoo dispatcher — to swap models, edit `.env`,
  `make kurpatov-wiki-compiler-down`, `make wiki-compiler`. Hot-swap is out of scope.
- Not load-balanced — one container, one GPU. If saturation becomes a
  problem, we add concurrency knobs in vLLM, not a second container.
- Not multi-GPU — single Blackwell. Tensor-parallel across PCIe is slower
  than single-card inference for 70B-class models with no NVLink.

## Mode mutex with rl-2048
`wiki-compiler` and `rl-2048` both want the Blackwell.
forge has effectively two modes: **compiler mode** (this lab running,
`rl-2048` stopped) and **2048 mode** (`rl-2048` running, this lab
stopped). Bringing both up at once will OOM or fail
nvidia-container-toolkit GPU allocation.

Discipline:
```
make stop-all      # stops every lab
make wiki-compiler     # → inference mode
make rl-2048       # → 2048 mode (you do this only after make kurpatov-wiki-compiler-down)
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
- `${STORAGE_ROOT}/shared/models → /root/.cache/huggingface` — shared HF cache
  (same volume rl-2048 and kurpatov-wiki use; weights downloaded once,
  used by all three modes).

Quantization stack at default config:
- **Weights**: model-dependent. For the current `Qwen/Qwen3.6-27B-FP8`
  default, `--quantization fp8`. Past defaults used AWQ via Marlin
  kernels (`--quantization awq_marlin`); update the flag at compose
  level when swapping models. vLLM can auto-detect from
  `config.quantization_config` if `--quantization` is absent.
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

For the current `Qwen/Qwen3.6-27B-FP8` default at 128K context (was
`cyankiwi/Qwen3.6-27B-AWQ-INT4` at 64K through 2026-04-25; the AWQ-INT4
community quant exhibited identical T3 crash characteristics to FP8 —
see bench/F1+A8 — so the swap was driven by license clarity and tooling
stability, not bug fixing)
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
--hf-overrides.rope_scaling.factor 4.0
--hf-overrides.rope_scaling.original_max_position_embeddings 32768
```

Currently set to **128K** (YaRN factor 4.0); 64K is the minimum some agent
harnesses (e.g. Hermes Agent) accept. Below 128K some agentic flows
that carry a 50K+ token skill+context exceed the budget — see
bench `experiments/A8.md` for the diagnostic that drove the bump.

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
  the value of `INFERENCE_MODEL` in `.env` (currently `Qwen/Qwen3.6-27B-FP8`; see `forge/.env` and `phase-b-business-architecture/org-units/wiki-bench/configs/models.yml` for swap candidates).
- `INFERENCE_SERVED_NAME` — public model name in the OpenAI API
  (`/v1/models` returns this). Default: the value of `INFERENCE_SERVED_NAME` in `.env` (currently `qwen3.6-27b-fp8`).
- `INFERENCE_MAX_MODEL_LEN` — context window cap in tokens. Default:
  `131072` (YaRN factor 4.0; see `## Context extension (YaRN)` above).
  Bump from 64K to 128K landed 2026-04-25 to fit T3 prompt + body without
  truncation (see lab `experiments/A8.md` in bench).
- `HF_TOKEN` — optional, only needed if the chosen model is gated.
- `STORAGE_ROOT` — for the HF cache mount.

Output:
- An OpenAI-compatible HTTP endpoint at `https://${INFERENCE_DOMAIN}/v1/`
  (chat/completions, completions, models). Auth: `Authorization: Bearer
  ${VLLM_API_KEY}`.

## Invariants
1. `proxy-net` exists (created by `make network` in root) before
   `make wiki-compiler`.
2. `${INFERENCE_DOMAIN}` resolves to this host's public IP.
3. `INFERENCE_GPU_UUID` is not held by any other forge container (i.e.
   `rl-2048` is down).
4. `${STORAGE_ROOT}/shared/models` exists (created by `make setup`).
5. Caddy is up before external traffic can reach the endpoint —
   the active lab provides caddy automatically ().

## Status
Live (since 2026-04-25). Per-lab smoke at `tests/smoke.md` /
`tests/smoke.sh`; root dispatcher (`scripts/smoke.sh`) routes here
automatically when this lab is the active one (its caddy holds
:80/:443).

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

## Default chat-template kwargs (Qwen3 reasoning-off-by-default)

Qwen3-family models are reasoning-tuned: by default they emit a
`<think>...</think>` block before the visible answer. With
`--reasoning-parser qwen3` we extract that into the `reasoning` field
so `content` stays clean — but the **token cost is paid regardless**.
If the client sends `max_tokens` low (e.g. Hermes Agent's default
256), the entire budget can be burned on reasoning tokens, leaving
`content: null` and `finish_reason: length`. Visually on the client
this looks like an agent stalling mid-word ("**Fin..." truncation).

Fix: bake `enable_thinking=false` as the server-side default for
Qwen3.6, regardless of what the client sends:

```
--default-chat-template-kwargs.enable_thinking false
```

Requests that explicitly pass `chat_template_kwargs.enable_thinking:
true` still get reasoning. The default just shifts to off, so naive
clients (Hermes Agent, raw OpenAI SDK with no extra_body, etc.) get
concise responses by default.

When swapping to a non-reasoning model (e.g. Llama 3.3 70B Instruct,
Gemma 3 27B), this flag is harmless — the model just ignores the
chat-template kwarg. When swapping to a different reasoning-tuned
family (e.g. DeepSeek-R1), check whether their template uses the
same `enable_thinking` key or a different one (`reasoning`,
`enable_chain_of_thought`, …) and adjust accordingly.

## Operations

### Model swap checklist
A model swap is **not** just an `INFERENCE_MODEL=` edit. Walk through:

1. Confirm the target model exists on HuggingFace at the spelled
   path. Many community quants are misnamed (e.g. cyankiwi's
   `Qwen3.6-27B-AWQ-INT4` is actually compressed-tensors INT4, not
   AWQ — the name is misleading).
2. Inspect `config.json` to confirm:
    - Quantization scheme (AWQ / compressed-tensors / FP8 / etc.).
    - Native `max_position_embeddings` — if smaller than
      `INFERENCE_MAX_MODEL_LEN`, you need YaRN.
    - Architecture name. Multimodal models (`*ForConditionalGeneration`)
      load extra MM components even when run text-only.
3. Decide quantization flag. Default behaviour: drop the
   `--quantization` line and let vLLM auto-detect from
   `config.quantization_config`. Force only when override is needed.
4. Pick parsers. See
   [ADR 0002](docs/adr/0002-per-model-parsers.md) and the lookup
   table there. Update both `--tool-call-parser` and
   `--reasoning-parser` in `phase-b-business-architecture/org-units/wiki-compiler/docker-compose.yml`.
5. Update YaRN params. The defaults
   (`factor=2.0, original=32768`) are tuned for Qwen3+ family.
   Other families (Llama, Mistral, Gemma) have different
   `original_max_position_embeddings` and may use different
   `rope_type` (e.g. `linear`, `dynamic`).
6. Update `.env`:
    - `INFERENCE_MODEL` — full HF id.
    - `INFERENCE_SERVED_NAME` — short slug for `/v1/models`.
    - `INFERENCE_MAX_MODEL_LEN` — keep ≥ 64K so Hermes Agent can connect.
    - `HF_TOKEN` — set if the new model is gated.
7. Mode-mutex: `make rl-2048-down` if it's running.
8. `make kurpatov-wiki-compiler-down && make wiki-compiler`.
9. `make kurpatov-wiki-compiler-logs`. Watch for `Application startup complete`,
   then run a sanity curl (see `## Sanity tests` below).
10. If healthy, **manually verify a tools request** before assuming
    the agent client will work. The HTTP 200 from vLLM is a weaker
    signal than a well-formed `tool_calls[]` in the response body.

### Sanity tests after model swap
Three curls in order, increasing complexity. Set `$VLLM_API_KEY`,
`$INFERENCE_DOMAIN`, `$INFERENCE_SERVED_NAME` from `.env` first.

```
# 1. Endpoint up + auth + model loaded.
curl -fsS https://$INFERENCE_DOMAIN/v1/models \
  -H "Authorization: Bearer $VLLM_API_KEY" | python3 -m json.tool

# 2. Plain chat completion.
curl -fsS https://$INFERENCE_DOMAIN/v1/chat/completions \
  -H "Authorization: Bearer $VLLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"'$INFERENCE_SERVED_NAME'","messages":[{"role":"user","content":"calculate 2+2 and return result in json {result:N}"}],"max_tokens":256,"temperature":0}' \
  | python3 -m json.tool

# 3. Tool call. The crucial one — exposes parser misconfiguration.
curl -fsS https://$INFERENCE_DOMAIN/v1/chat/completions \
  -H "Authorization: Bearer $VLLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"'$INFERENCE_SERVED_NAME'","messages":[{"role":"user","content":"What is 47*53? Use the calculator tool."}],"tools":[{"type":"function","function":{"name":"calculator","description":"Eval","parameters":{"type":"object","properties":{"expr":{"type":"string"}},"required":["expr"]}}}],"tool_choice":"auto","max_tokens":256,"temperature":0}' \
  | python3 -m json.tool
```

The third response must show `finish_reason: "tool_calls"`, populated
`tool_calls[]`, and `content: null` (or empty) — anything else is a
parser mismatch (see ADR 0002 diagnostic table).

### Known harmless warnings during startup
These appear in `make kurpatov-wiki-compiler-logs` and **do not** indicate a
problem:

- `WARNING [argparse_utils.py:191] With 'vllm serve', you should
  provide the model as a positional argument …` — deprecation notice
  for `--model`. We use `--model` deliberately to keep the model id
  pinned by env var; we'll migrate when v0.13 actually lands.
- `Qwen2VLImageProcessorFast is deprecated. The 'Fast' suffix has
  been removed; use Qwen2VLImageProcessor instead.` — internal
  transformers shim renaming, harmless.
- `The 'use_fast' parameter is deprecated and will be removed in a
  future version.` — same, harmless.
- `UserWarning: Input tensor shape suggests potential format
  mismatch: seq_len (16) < num_heads (48). This may indicate the
  inputs were passed in head-first format …` — emitted by FLA
  (Flash Linear Attention) on warmup with small seq_len batches; the
  shape is correct, the heuristic that emits this warning is overly
  aggressive at small sizes. Disappears once real prompts come in.

If any of these escalate to `ERROR` rather than `WARNING`, escalate
to the operator.

### Caddy survives the model swap
caddy is unaffected by `make kurpatov-wiki-compiler-down && make wiki-compiler`. The
`reverse_proxy vllm-inference:8000` directive caches no upstream
state; when the upstream comes back, requests start flowing again
on the next health interval. No `make caddy-down` needed unless
`INFERENCE_DOMAIN` changes (rare).

## Open questions
- Do we ever want a second model loaded simultaneously (e.g. a small
  draft model on RTX 5090 for speculative decoding)? Not now; the RTX
  5090 stays with `kurpatov-wiki` for transcription. Revisit if the
  benchmark workload makes throughput a bottleneck.
- Do we want vLLM's `/metrics` (Prometheus) wired into a future
  observability subsystem? Not now; surface to the operator if the
  question becomes real.
