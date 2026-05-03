# ADR 0006 — inference subsystem: deploy-session findings (2026-04-25)

## Status
Accepted (2026-04-25). Amends ADR 0005.

## Context
ADR 0005 introduced the `inference/` subsystem from the design side.
The first end-to-end deploy on the Blackwell, on the same day,
turned up several theory-vs-reality gaps. This ADR captures them
so the assumptions baked into ADR 0005 do not silently rot when the
next operator reads it cold.

The inference subsystem has been verified live, end-to-end, against
the actual Hermes Agent client. What follows is what changed
between the design ADR and the running service.

## What didn't survive contact

**Image source**. ADR 0005 picked NGC's `nvcr.io/nvidia/vllm` for
"first-class Blackwell support". The exact tag (`25.03-py3`) was
unreachable at deploy (`manifest unknown`). Switched to Docker Hub
stable `vllm/vllm-openai:v0.19.1-cu130-ubuntu2404`, which works on
SM120 with our `nvidia-driver-590-open` first-try. Lesson: prefer
the registry that publishes a release-versioned tag, not a
date-versioned one we'd guess at; Docker Hub vLLM has caught up
with Blackwell during 2026 and the historical NGC advantage no
longer applies for our use case.

**KV cache compression**. ADR 0005 chose TurboQuant K4V4 as the
default. v0.19.1 stable rejects `--kv-cache-dtype turboquant_4bit_nc`
as `invalid choice` — TurboQuant lives only in nightlies as of
2026-04. Fell back to FP8 KV cache (the documented stable
alternative). FP8 gives us 60+ GB pool / 26× concurrency at 64K on
the current model; we'll re-enable TurboQuant when it ships in a
stable release.

**Default model**. ADR 0005 picked
`Qwen/Qwen3-72B-Instruct-AWQ`. That HF id does not exist —
Qwen's official Qwen3 AWQ tops at 32B. Briefly tried
`Qwen/Qwen3-32B-AWQ` (works, well-behaved); eventually settled on
`cyankiwi/Qwen3.6-27B-AWQ-INT4` (community compressed-tensors INT4
quant of Qwen's official Qwen3.6-27B). Lesson: search HF for the
spelled id before pinning it in design docs.

**Quantization flag**. The community AWQ-INT4 model is actually
quantized with compressed-tensors, not AWQ — a misleading filename.
Pinning `--quantization awq_marlin` produced a Pydantic validation
error at vLLM startup. Removed the flag entirely — vLLM
auto-detects from `config.quantization_config` and picks the
right kernel (MarlinLinearKernel via the
`compressed_tensors_wNa16` path in this case). General rule
adopted: do not pin `--quantization` unless overriding.

## What was missing from ADR 0005

**Tool-call parsing** is required for any agent client. Naïvely-
deployed vLLM returns HTTP 400 to any request carrying
`tools:[...]`. Added `--enable-auto-tool-choice` plus
`--tool-call-parser <name>`.

**The parser is family-specific**. First pass with
`--tool-call-parser hermes` worked for trivial single-arg
calculator calls but silently wedged Hermes Agent on real
multi-tool prompts — Qwen3.6's actual XML-tagged tool-call output
isn't what `hermes` parser expects. Switching to
`--tool-call-parser qwen3_xml` fixed it. The full lookup table
plus the diagnostic symptom→cause mapping now lives at
[`inference/docs/adr/0002-per-model-parsers.md`](../../phase-c-information-systems-architecture/application-architecture/wiki-compiler/docs/adr/0002-per-model-parsers.md).

**Reasoning extraction**. Modern open-weight models (Qwen3, R1,
GLM-Reasoning) emit `<think>...</think>` blocks. Without
`--reasoning-parser <name>`, the closing tag and the chain-of-
thought leak into `message.content`, which downstream agents
mishandle. Added `--reasoning-parser qwen3` for the default model.

**Hermes Agent's 64K minimum**. The laptop client refuses to
initialize against a model whose `max_model_len < 65536`. Qwen3.6
is natively 32K; bumped to 64K via YaRN rope-scaling
(`--hf-overrides.rope_scaling.rope_type=yarn factor=2.0
original=32768`). Older `--rope-scaling '{json}'` flag is gone
in v0.19; dot-notation through `--hf-overrides` is the working
path, and it dodges YAML's folded-scalar JSON-quote-stripping bug
in `command:` blocks.

## What was right in ADR 0005

The architectural choices held up:

- Single subsystem `inference/`, single container `vllm-inference`,
  Blackwell-only, no TP — single-card inference is faster than
  PCIe TP for 27-72B class models, confirmed.
- vLLM API key in `--api-key`, no caddy basic auth on this site
  block — Hermes Agent connects with `Authorization: Bearer ...`
  cleanly, no SDK breakage.
- Mode mutex with rl-2048 — verified by `make rl-2048-down && make
  inference`. Smooth swap.
- Shared HF cache at `${STORAGE_ROOT}/models` — model weights
  downloaded once, reusable by rl-2048 in rl-2048 mode.

## Decision
Amend ADR 0005 with the deploy-time discoveries above. The
operating-truth versions of decisions live in `inference/SPEC.md`
(now with an explicit `## Operations` section) and
`inference/docs/adr/0002-per-model-parsers.md` (the parser ADR).

For onboarding readers: read **ADR 0005 + this ADR + ADR 0002 +
SPEC.md** in that order. ADR 0005 establishes the design, this ADR
flags where it diverged, ADR 0002 captures the parser layer that
ADR 0005 didn't anticipate, and SPEC.md is the up-to-date how-to.

## Consequences

**Positive.**
- New operators don't have to rediscover the deploy-time gotchas.
- The parser ADR codifies a layer of the OpenAI-compatibility
  abstraction that's easy to dismiss as "just glue" until it
  silently breaks an agent.
- SPEC.md now includes a model-swap checklist and a list of
  known harmless warnings — both extracted from this session's
  log review.

**Negative / accepted.**
- ADR drift: the next vLLM release may add a TurboQuant stable
  path or rename parsers, making chunks of this ADR obsolete. The
  operator is expected to re-verify against `vllm serve --help` on
  the live container, not against this document, when troubleshooting.
- Some of these findings (specifically the misleading model
  filename) are HF-ecosystem hygiene issues, not architectural
  ones; they're documented here mainly so the next time we hit a
  Pydantic quantization-mismatch error we recognize the shape.

## Touched files
- New: `phase-f-migration-planning/adr/0006-inference-deploy-session-2026-04-25.md` (this).
- New: `inference/docs/adr/0002-per-model-parsers.md`.
- Edits: `inference/SPEC.md` (operations + sanity-test sections,
  parser/reasoning section), `inference/docker-compose.yml`
  (image, KV cache, parsers, reasoning, YaRN), `.env.example`
  (default model, max-model-len, key generation hint).


## Measurable motivation chain
Per [P7](../../phase-preliminary/architecture-principles.md) — backfit:

- **Driver**: 2026-04-25 inference-deploy session needed an
  ADR-recorded play-by-play to prevent re-deriving its
  decisions.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: deploy decisions captured + cross-linked from
  Phase F migration-plan.
- **Measurement source**: experiment-closure: G2 (MoE faster-inference experiment closure)
- **Contribution**: migration discipline reduces deploy-incident class; contributes to Quality KR.
