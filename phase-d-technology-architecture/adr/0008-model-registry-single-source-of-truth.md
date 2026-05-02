# ADR 0008 — model registry as single source of truth

## Status
Accepted (2026-04-25). Amends ADR 0005 (inference subsystem) and ADR 0007
(labs restructure).

## Context

After ADR 0007 the compiler subsystem became `phase-c-information-systems-architecture/application-architecture/wiki-compiler/`.
But the configuration of which model to serve (and with what flags) was
spread across **three independent files**:

| parameter                         | location                                              |
| --------------------------------- | ----------------------------------------------------- |
| model HF id, served name          | `forge/.env: INFERENCE_MODEL`, `INFERENCE_SERVED_NAME` |
| max-model-len                     | `forge/.env: INFERENCE_MAX_MODEL_LEN`                 |
| YaRN factor, rope_type, orig_max  | `phase-c-information-systems-architecture/application-architecture/wiki-compiler/docker-compose.yml`      |
| kv-cache dtype, parsers, quant    | same compose file (hard-coded args)                   |
| max_model_len (again)             | `phase-c-information-systems-architecture/application-architecture/wiki-bench/configs/models.yml`         |

Bench's `run-battery.sh` loaded its `models.yml`, patched `forge/.env`
with three fields, and ran `make compiler-down/up`. It **did not** patch
the compose file's hard-coded `--hf-overrides.rope_scaling.factor`.

The 2026-04-25 A8 incident demonstrated the failure mode:

1. Operator (this session) bumped both `.env: INFERENCE_MAX_MODEL_LEN=131072`
   and `compose: factor 4.0` for 128K context.
2. Operator ran `run-battery.sh qwen3.6-27b-fp8`.
3. Battery patched `.env: INFERENCE_MAX_MODEL_LEN=65536` (because
   `bench/configs/models.yml: qwen3.6-27b-fp8.max_model_len = 65536`,
   the old value).
4. Battery did not touch the compose file, so `factor 4.0` remained.
5. vLLM started with `max-model-len 65536` + YaRN factor for 128K —
   **silently inconsistent**, no error.

The fix at the time was to also patch `bench/models.yml` to 131072
(commit 97aa0b3). That patched the symptom, not the cause.

## Decision

Promote the model registry to **single source of truth** for compiler
serving configuration:

1. **Registry**: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/configs/models.yml` —
   one entry per model with all serving parameters
   (HF id, served name, quant, kv_cache, max_model_len, rope_scaling,
   parsers, chat_template_kwargs, tensor_parallel_size, plus optional
   batch-control fields `bench_tier` / `bench_skip` for the bench client).

2. **Active selector**: `forge/.env: INFERENCE_ACTIVE_MODEL_ID=<id>`.
   Replaces the previous three fields (`INFERENCE_MODEL`,
   `INFERENCE_SERVED_NAME`, `INFERENCE_MAX_MODEL_LEN`). `<id>` must
   match an entry in the registry.

3. **Render step**: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/bin/load-active-model.sh`
   reads the registry, looks up the active id, writes
   `phase-c-information-systems-architecture/application-architecture/wiki-compiler/.env.active-model` (gitignored)
   with `MODEL_*` env vars. Compose's `command:` references those
   `${MODEL_*}` vars.

4. **Compose stack**: two `--env-file`s in order:
   `forge/.env` (secrets, infra, active selector) →
   `phase-c-information-systems-architecture/application-architecture/wiki-compiler/.env.active-model` (rendered model
   params, overrides if any). The compose `command:` uses
   `${MODEL_HF}`, `${MODEL_MAX_MODEL_LEN}`, `${MODEL_ROPE_FACTOR}`, etc.

5. **`make wiki-compiler` chains** `bin/load-active-model.sh`
   before `docker compose up -d`. Operators never edit
   `.env.active-model` directly — they edit the registry or the
   active selector and `make compiler-down && make compiler` to apply.

6. **Bench is a client**:
   - Reads `phase-c-information-systems-architecture/application-architecture/wiki-compiler/configs/models.yml` directly
     (no second registry).
   - `run-battery.sh` iterates over registry entries, patches **only**
     `forge/.env: INFERENCE_ACTIVE_MODEL_ID`, calls `make
     compiler-down/up`, runs `./run.sh`.
   - `run.sh` resolves the served name from
     `GET ${INFERENCE_BASE_URL}/models[].id`, not from `.env`. The
     bench branch slug is built from the live served name (so a
     misalignment between selector and reality surfaces as a preflight
     fail, not a silent miscredit).

## Consequences

**Positive.**

- Impossible to have `max_model_len` and `rope_scaling.factor` on
  different sides of the 64K/128K boundary — they live in the same
  yaml entry.
- One file to edit when adding a new model (registry).
- Bench stops co-owning model configuration. Smaller surface, cleaner
  client/server split.
- `make compiler-up` is idempotent against the registry: re-running
  with the same active id always produces the same vLLM command line.
- New invariant for compiler smoke: `(registry, .env, compose, running
  vLLM)` are consistent. Drift is a smoke failure.

**Negative / accepted.**

- One-time migration: rewrite compose `command:` to use `${MODEL_*}`
  vars, delete inline hard-coded args, delete bench's separate
  `models.yml`, repoint bench scripts. Touch about 10 files; backwards
  incompatible (`forge/.env` schema changed — `INFERENCE_MODEL` /
  `INFERENCE_SERVED_NAME` / `INFERENCE_MAX_MODEL_LEN` removed,
  `INFERENCE_ACTIVE_MODEL_ID` added).
- compose-time conditionality is limited: the env-substitution
  approach can only render flags that are present **for every** model.
  Models without YaRN scaling must still set `factor: 1.0` and
  `original_max_position_embeddings == max_model_len` (no-op rope
  scaling). If we later add models that need disjoint flag sets, we
  may need full template rendering (variant B in the design doc) — but
  for the current cohort (Qwen3.x, Mistral, Devstral, Nemotron, Llama
  with YaRN), env substitution is enough.

## Touched files

- New: `phase-d-technology-architecture/adr/0008-model-registry-single-source-of-truth.md` (this).
- New: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/configs/models.yml`.
- New: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/bin/load-active-model.sh`.
- New: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/.gitignore` (ignores `.env.active-model`).
- Modified: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/docker-compose.yml` (env subst).
- Modified: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/Makefile` (chain load-active-model).
- Modified: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/SPEC.md` (registry + selector).
- Modified: `phase-c-information-systems-architecture/application-architecture/wiki-compiler/tests/smoke.{md,sh}` (consistency check).
- Modified: `forge/.env` (`INFERENCE_ACTIVE_MODEL_ID` replaces three fields).
- Modified: `forge/.env.example` (mirror).
- Deleted: `phase-c-information-systems-architecture/application-architecture/wiki-bench/configs/models.yml` (registry is on compiler side).
- Modified: `phase-c-information-systems-architecture/application-architecture/wiki-bench/run-battery.sh` (only patches selector).
- Modified: `phase-c-information-systems-architecture/application-architecture/wiki-bench/run.sh` (preflight via `/v1/models`).
- Modified: `phase-c-information-systems-architecture/application-architecture/wiki-bench/SPEC.md` (client of registry).
- Modified: `phase-d-technology-architecture/architecture.md` (registry layer in topology).

## Alternatives considered

- **Keep the status quo**: each parameter in its own file, bench can
  patch the parts it knows about. Rejected — A8 incident showed this
  is fragile and silent.
- **Full template rendering** (variant B): generate `docker-compose.yml`
  from the registry on every up. Considered, but adds magic — compose
  is no longer the source of truth for the running command. Deferred
  until env-substitution proves insufficient.
- **Multi-registry** (compiler-registry for runtime, bench-registry
  for batch metadata): rejected — adds two-file-must-stay-in-sync
  problem. Encoding both layers in one yaml with compiler ignoring
  `bench_*` fields is simpler.


## Measurable motivation chain (OKRs)
Per [P7](../../phase-preliminary/architecture-principles.md) — backfit:

- **Driver**: model swaps (G2, G3, future) need a single
  source-of-truth registry.
- **Goal**: Architect-velocity (G* experiments cite the
  registry instead of re-deriving model paths).
- **Outcome**: configs/models.yml in wiki-compiler is the
  registry; ADRs cite this file for any model change.
- **Measurement source**: quality-ledger: pre_prod_share (per ADR 0021)
