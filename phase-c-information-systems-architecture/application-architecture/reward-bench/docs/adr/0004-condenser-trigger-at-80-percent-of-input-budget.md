# ADR 0004 — Condenser trigger at 80% of effective input budget (~80000 tokens for 128K models)

## Status

Accepted (2026-05-13). Active.

## Context

[ADR 0001](0001-condenser-uses-same-model-as-bench.md) decided that
the condenser uses the same model as the bench target. The bench
model serves at `max_model_len=131072` (per
[SPEC.md](../../SPEC.md) §"Author-stage inference context"). Cycle 21
made `LlmCondenser` token-aware: it gates compaction on a
`trigger_tokens` threshold from `CondenserConfig`. The remaining
question: **what value should that threshold be?**

The legacy `_bak/bin/campaign_tier1.sh` set
`--condenser-trigger-tokens 40000` (~30 % of `max_model_len`). That
value was chosen for a setup that ran the condenser on a
**different, smaller model** on the secondary 5090 GPU. The
condenser model had a smaller effective context; conservative
trigger avoided pushing the small model past its own limit.

In our setup the condenser IS the bench model (per ADR 0001), with
`max_model_len=131072`. Triggering at 40000 fires the condenser at
30 % of budget — well before the context is anywhere near its
limit. Cycle-20 live verification showed this over-aggressive
firing inflated cycle-12 wall time **10×** (56 s → 561 s) with no
quality benefit (`mean_score` unchanged: 3361 → 3410).

## Decision

The default `_CONDENSER_TRIGGER_TOKENS` is **80000** (~80 % of the
effective input budget).

Derivation:

    max_model_len          = 131_072   (qwen3.6-27b-awq serving)
    output max_tokens      =  32_768   (agent_loop._call_model default)
    effective_input_budget = 131_072 - 32_768 = 98_304
    trigger ≈ 0.8 × 98_304 = 78_643 → round to 80_000

Headroom of ~18 K tokens between trigger and effective input limit
gives room for the **last turn before compaction** to be processed
without overflow.

## Consequences

### Positive

- **Short bench runs stay fast.** Cycle 12 strict (30 iters) stays
  at ~56 s. Cycle 18-20 ballooned it to 561 s; cycle 21 brings it
  back.
- **Compaction fires near the context limit, where it adds value.**
  Long campaigns (500-iter, per [ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md))
  will trigger compaction in their later iterations where 128 K
  budget is actually under pressure.
- **No quality regression.** Cycle 20 verified `mean_score` is
  unchanged between condenser-off (3361) and condenser-on-aggressive
  (3410). The condenser doesn't help model quality at short
  iterations — it only matters for budget management.

### Negative

- **Imprecise token estimate.** The `LlmCondenser` uses a
  4-chars-per-token heuristic. Real token counts depend on the
  tokenizer; estimate may be off by ±30 %. Mitigation: 18 K
  headroom between trigger and budget absorbs the error.
- **Diverges from `_bak` legacy.** Anyone comparing leaderboard
  numbers under our settings vs `_bak` settings should know that
  `trigger_tokens` is one of the differences.
- **Tied to qwen3.6's 131K budget.** Models with smaller
  `max_model_len` would over-trigger. Future cycle should compute
  `trigger_tokens` per `ModelTarget` (e.g.
  `0.8 * (target.max_model_len - 32768)`).

### Reverting

The constant lives in
`src/reward_bench/frameworks/main.py` as `_CONDENSER_TRIGGER_TOKENS`.
A future cycle should lift it onto `BenchConfig` so it is
overridable per run; today the only way to override is to monkey-
patch the module constant.

## Alternatives considered

### A. Keep the legacy `40000` (~30 % of budget)

Faithful to `_bak`. **Rejected** because it over-fires; cycle 20
data showed walltime inflation without quality benefit.

### B. Trigger at the limit (`98000`)

Maximum context usage before compaction. **Rejected** because the
4-chars-per-token estimate may be off; running right up to the
limit risks vLLM rejecting a request as too long.

### C. Per-model `trigger_tokens` derived from `ModelTarget.max_model_len`

Cleanest long-term. **Deferred** — this ADR's `80000` is the right
default for the current `qwen3.6-27b-awq` (max_model_len=131072).
Future cycle adds the derivation so smaller-context models scale
down.

### D. Token-count from a real tokenizer (transformers / tiktoken)

Accurate. **Deferred** — adds a heavy import dependency to a
critical path. The 4-chars-per-token heuristic with 18 K headroom
is enough for the current setup. Cycle later when token accounting
becomes the dominant error.

## Implementation pointers

- `src/reward_bench/frameworks/main.py` — the `_CONDENSER_TRIGGER_TOKENS = 80000`
  module constant.
- `src/reward_bench/adapters/llm_condenser.py` — the `_estimate_tokens`
  helper using the 4-chars-per-token heuristic; the token gate in
  `LlmCondenser.condense`.
- `tests/reward_bench/adapters/test_llm_condenser.py` — the
  pass-through test pins the token gate behavior.

## Cross-references

- [SPEC.md §"Author-stage inference context"](../../SPEC.md)
- [Lab ADR 0001](0001-condenser-uses-same-model-as-bench.md) — same-model
  condenser; this ADR builds on that by relaxing the trigger.
- [Lab ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md)
  — bench knob defaults. `trigger_tokens` is NOT in `BenchConfig`
  yet (queued); when lifted it inherits this ADR's value as default.
- `_bak/bin/campaign_tier1.sh` — the source-of-truth document for
  the legacy `40000` value.
