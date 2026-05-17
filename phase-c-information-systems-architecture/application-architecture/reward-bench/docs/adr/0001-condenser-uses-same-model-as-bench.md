# ADR 0001 — Condenser uses the same model as the model under bench

## Status

Accepted (2026-05-13). Active.

## Context

[SPEC.md](../../SPEC.md) §"Author-stage inference context" describes
the Stage-1 author loop running with **128 K input + output context**
and a **condenser** that summarises older turns when prompt + reserved
output exceeds the budget.

The legacy `_bak/bin/campaign_tier1.sh` wired the condenser to a
**separate, smaller** model (`condenser-llama31-8b` on the secondary
RTX 5090), via `--condenser-shim`, `--condenser-model`,
`--condenser-trigger-tokens`, `--condenser-keep-recent` flags. Two
containers, two registry entries, two cache stores.

Three observations against a separate condenser:

1. **Operational drag.** Second container lifecycle, second GPU mutex,
   second registry entry, version-skew risk.
2. **The bench model already has 128 K of context.** vLLM serves
   `qwen3.6-27b-awq` with `--max-model-len 131072`; summarisation fits
   comfortably inside that budget.
3. **Cross-model comparability.** A/B comparisons are cleaner when
   every model is its own summariser — no "model A had a better
   condenser" confound.

## Decision

The condenser uses the **same `ModelTarget`** as the model under
bench. There is no separate condenser deployment.

Concretely:

- `CondenserConfig.model_id` defaults to the bench model's `id`.
- The condenser adapter calls the **same vLLM endpoint** that the
  agent loop uses for the bench. No `--condenser-shim` URL, no second
  container.
- The orchestrator (`reward_bench.frameworks.main`) constructs both
  the bench-model `ChatPort` and the condenser using one `ModelTarget`
  picked from `MODEL_REGISTRY`.

## Consequences

### Positive

- **Simpler topology.** One vLLM container per bench run; no second
  GPU slot; no condenser-vs-bench-model version skew.
- **No second registry entry.** `MODEL_REGISTRY` is the catalogue of
  evaluable models; it doesn't need separate condenser model entries.
- **Cleaner A/B.** Cross-model comparisons compare each model
  end-to-end including its own self-summarisation behaviour.
- **Lower memory footprint at session start.** No need to keep a
  llama-3.1-8b warm on the 5090 while the bench runs.

### Negative

- **Condenser eats into agent context budget.** Mitigation:
  `keep_recent` keeps recent turns verbatim; older turns collapse to a
  single short summary. Net: fewer tokens than no condensing.
- **If the bench model is poor at summarisation, the condenser is
  poor.** A model that can't summarise its own history probably can't
  solve the task — the bench result remains meaningful.
- **Throughput cost.** One extra inference per `condense()`. Triggers
  only after `trigger_tokens` (default 40 K).

### Reverting

`CondenserConfig.model_id` is configurable; a future cycle can point it
at a different `ModelTarget`. Only the default changes.

## Alternatives considered

### A. Separate smaller condenser model (legacy `_bak`)

`llama-3.1-8b-nvfp4` on the 5090, separate container, separate registry.
**Rejected**: operational drag and comparability confound (above).

### B. No condenser at all

Fail when context exceeds budget. **Rejected**: tier 3-4 accumulates
context faster than tier 1; bench reach depends on sustained context.

### C. Sliding window without summarisation

Drop oldest turns at trigger. **Rejected**: tier 1 benefits from
remembering early dev-runner feedback and SKILL.md; truncation drops
information the model is using.

## Implementation pointers

- `src/reward_bench/entities/condenser_config.py` — `model_id` field.
- `src/ports/condenser.py` — `CondenserPort` Protocol. Default
  `NullCondenser` at `src/reward_bench/adapters/null_condenser.py`.
- `src/reward_bench/adapters/llm_condenser.py` — calls the bench-model
  vLLM endpoint.
- `src/reward_bench/frameworks/main.py` — wires the condenser using the
  bench `ModelTarget`.

## Cross-references

- [SPEC.md §"Author-stage inference context"](../../SPEC.md)
- [Forge ADR 0029 — reward-bench](../../../../../phase-preliminary/adr/0029-reward-bench.md)
- [Forge ADR 0028 — inference mode](../../../../../phase-preliminary/adr/0028-inference-mode.md) — the single vLLM endpoint pattern this ADR builds on.
