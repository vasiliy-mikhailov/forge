# ADR 0004 — Condenser trigger at 80% of effective input budget (~80000 tokens for 128K models)

## Status

Accepted (2026-05-13). Active.

## Context

Per [ADR 0001](0001-condenser-uses-same-model-as-bench.md), the
condenser is the bench model, serving at `max_model_len=131072`.
`LlmCondenser` gates compaction on a `trigger_tokens` threshold from
`CondenserConfig`. Question: **what value?**

The legacy `_bak/bin/campaign_tier1.sh` used `40000` (~30 % of budget),
sized for a smaller condenser model on the secondary GPU.

With the same-model condenser, triggering at 40000 fires at 30 % of
budget — far from the limit. Live verification showed this inflated
short-run wall time **10×** (56 s → 561 s) with no quality benefit
(`mean_score`: 3361 → 3410).

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

- **Short runs stay fast.** 30-iter runs stay at ~56 s.
- **Compaction fires where it matters.** 500-iter campaigns trigger
  late, when the 128 K budget is actually under pressure.
- **No quality regression.** `mean_score` unchanged between
  condenser-off (3361) and condenser-on-aggressive (3410).

### Negative

- **Imprecise token estimate.** 4-chars-per-token heuristic may be off
  ±30 %. Mitigation: 18 K headroom absorbs the error.
- **Diverges from `_bak`.** Cross-config comparisons must note this.
- **Tied to qwen3.6's 131 K budget.** Smaller-context models would
  over-trigger; future cycle should derive `trigger_tokens` per
  `ModelTarget` as `0.8 * (max_model_len - 32768)`.

### Reverting

Constant lives in `src/reward_bench/frameworks/main.py` as
`_CONDENSER_TRIGGER_TOKENS`. Future cycle should lift onto
`BenchConfig` for per-run override.

## Alternatives considered

### A. Keep legacy `40000` (~30 %)

**Rejected**: over-fires; inflates walltime without quality benefit.

### B. Trigger at the limit (`98000`)

**Rejected**: heuristic may overshoot; vLLM would reject as too long.

### C. Per-model `trigger_tokens` from `ModelTarget.max_model_len`

**Deferred**: `80000` is correct for current `qwen3.6-27b-awq`.

### D. Real tokenizer (transformers / tiktoken)

**Deferred**: heavy import on a hot path; heuristic + headroom suffices.

## Implementation pointers

- `src/reward_bench/frameworks/main.py` — `_CONDENSER_TRIGGER_TOKENS = 80000`.
- `src/reward_bench/adapters/llm_condenser.py` — `_estimate_tokens`
  helper; token gate in `LlmCondenser.condense`.
- `tests/reward_bench/adapters/test_llm_condenser.py` — pins the gate.

## Cross-references

- [SPEC.md §"Author-stage inference context"](../../SPEC.md)
- [Lab ADR 0001](0001-condenser-uses-same-model-as-bench.md) — same-model condenser.
- [Lab ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) — bench knob defaults.
- `_bak/bin/campaign_tier1.sh` — legacy `40000` source.
