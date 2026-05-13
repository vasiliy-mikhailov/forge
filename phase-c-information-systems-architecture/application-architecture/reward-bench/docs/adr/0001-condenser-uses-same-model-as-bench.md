# ADR 0001 — Condenser uses the same model as the model under bench

## Status

Accepted (2026-05-13). Active.

## Context

[SPEC.md](../../SPEC.md) §"Author-stage inference context" describes
the Stage-1 author loop running with **128 K input + output context**
and a **condenser** that summarises older turns when prompt + reserved
output exceeds the budget so the loop can run as long as the model can
still make progress.

The legacy `_bak/bin/campaign_tier1.sh` wired the condenser to a
**separate, smaller** model (`condenser-llama31-8b` running on the
secondary RTX 5090 GPU), exposed via `--condenser-shim`,
`--condenser-model`, `--condenser-trigger-tokens`,
`--condenser-keep-recent` flags. Pattern was: bench model runs on the
Blackwell, condenser model runs on the 5090, two containers, two model
registry entries, two cache stores.

Re-thinking under CATS: do we *want* a separate condenser model?

Three observations:

1. **Operational drag.** A separate condenser doubles the operational
   surface — second container lifecycle, second GPU mutex, second
   model-registry entry, version-skew risk between condenser and bench
   model.
2. **The bench model already has 128 K of context.** vLLM serves
   `qwen3.6-27b-awq` with `--max-model-len 131072`; a summarisation
   call to the same model fits comfortably inside that budget. The
   condenser doesn't *need* a different model to do its job.
3. **Cross-model comparability.** When the bench compares model A vs
   model B at Tier 3-4, having both condensers be the *same* model as
   the bench target makes the comparison cleaner: every model is its
   own summariser. No "model A had a better condenser" confound.

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

- **Condenser eats into agent context budget.** Each summarisation
  call consumes input + output tokens from the same model's effective
  budget. Mitigation: `keep_recent` keeps the most recent turns
  verbatim; older turns are replaced by a single short summary turn.
  The net effect is fewer tokens spent on context than no condensing
  at all.
- **If the bench model is poor at summarisation, the condenser is
  poor.** But a model that can't summarise its own conversation
  history probably can't solve the task either, so the bench result
  is still meaningful — just worse all around.
- **Throughput cost.** Each `condense()` call is one extra inference
  request. Acceptable; condensing triggers only after
  `trigger_tokens` (default 40 K) are accumulated.

### Reverting

The decision can be reversed cycle-by-cycle if needed: `CondenserConfig`
already carries `model_id`, so a future cycle could set it to a
different `ModelTarget`. The default behaviour is what changes; the
abstraction supports either choice.

## Alternatives considered

### A. Separate smaller condenser model (legacy `_bak`)

Use e.g. `llama-3.1-8b-nvfp4` on the 5090, separate vLLM container,
separate model registry. **Rejected** because of operational drag and
the comparability confound described above.

### B. No condenser at all

Cap the agent loop at whatever the model's context window can hold;
fail when context exceeds budget. **Rejected** because tier 3-4 will
accumulate context faster than tier 1 (orchestrator calls + node-level
LLM calls inside the submitted graph) and the bench's reach depends on
sustained context.

### C. Sliding window without summarisation

Drop oldest turns when budget hits trigger. **Rejected** because tier 1
specifically benefits from remembering the early dev-runner feedback
and the SKILL.md spec; losing those by simple truncation drops
information the model is using.

## Implementation pointers

- `src/reward_bench/entities/condenser_config.py` — already exists
  (cycle 13). `model_id` field carries the chosen condenser model id.
- `src/reward_bench/use_cases/condenser_port.py` — already exists
  (cycle 14). `NullCondenser` is the default for cases below the
  trigger.
- `src/reward_bench/adapters/llm_condenser.py` — cycle 16. Will
  call the bench-model vLLM endpoint to summarise older turns.
- `src/reward_bench/frameworks/main.py` — cycle 17. Wires the
  condenser using the same `ModelTarget` that drives the bench.

## Cross-references

- [SPEC.md §"Author-stage inference context"](../../SPEC.md)
- [Forge ADR 0029 — reward-bench](../../../../../phase-preliminary/adr/0029-reward-bench.md)
- [Forge ADR 0028 — inference mode](../../../../../phase-preliminary/adr/0028-inference-mode.md) — the single vLLM endpoint pattern this ADR builds on.
