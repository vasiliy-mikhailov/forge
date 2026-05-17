# ADR 0003 — Bench defaults: 500 iters, 10 trials, temperature 0.7, 128 K context, same-model condenser

## Status

Accepted (2026-05-13). Active.

## Context

The minimum-viable rewrite for `qwen3.6-27b-awq` produced
`mean_score=3360.8`. The legacy `_bak/bin/campaign_tier1.sh` campaign
for the same model produced **~15920**. The 4.7× gap is a
**knob-setting** difference, not a model difference.

Gap analysis:

| Lever | `_bak` | minimum-viable rewrite | Approx. factor |
| ----- | ------ | ---------------------- | -------------- |
| `max_iters` | **500** | 30 | 16× turn budget |
| `n_trials` | **10** | 1 | 1.5-2× lift on reported mean |
| `temperature` | **0.7** | 0.0 (greedy) | 1.2-1.5× from exploration |
| Condenser | llama-3.1-8b on 5090 | none (seam only) | enables higher `max_iters` |
| `max_no_improve` | 999999 | n/a | forces continued iteration |
| `finish_floor` | 0 | n/a | shape-only enforcement |

Product ≈ 5-9×, matching the observed 4.7× gap within an order of
magnitude.

## Decision

The reward-bench defaults — values that `main()` and the multi-trial
use case use when no explicit config is supplied — are:

| Field            | Default   | Source                                          |
| ---------------- | --------- | ----------------------------------------------- |
| `max_iters`      | **500**   | `_bak/bin/campaign_tier1.sh: MAX_TURNS`         |
| `n_trials`       | **10**    | `_bak/bin/campaign_tier1.sh: N_TRIALS`          |
| `temperature`    | **0.7**   | `_bak/bin/campaign_tier1.sh: TEMPERATURE`       |
| `max_model_len`  | **131072**| SPEC.md §"Author-stage inference context"      |
| `condenser_model`| same as bench target | ADR 0001                              |
| `max_no_improve` | **999999**| `_bak/bin/campaign_tier1.sh`                    |
| `finish_floor`   | **0**     | `_bak/bin/campaign_tier1.sh`                    |
| `hard_wall_sec`  | **0**     | SPEC.md (disabled by default)                   |

Land as fields on a `BenchConfig` value object. Every leaderboard
publication must report the config used unless explicitly overridden.

## Consequences

### Positive

- **Closes the score-quality gap.** Targets the `_bak` 15.9 k baseline.
- **Surfaces real model differences.** High-iter + exploration
  temperature is what makes the leaderboard discriminate.
- **One source of truth.** All call sites (`main()`,
  `agent_loop._call_model`, multi-trial use case, condenser trigger)
  read `BenchConfig` instead of hardcoding.
- **Clean A/B.** Identical defaults across models; deltas reflect
  capability, not knob drift.

### Negative

- **Wall time.** 500 × 10 × ~2 s × 21 models ≈ 30+ GPU-hours per full
  leaderboard run. No longer a 60-second smoke.
- **Condenser blocking.** `max_iters=500` blows past 128 K on a single
  conversation; defaults ship but long runs await working condenser.
- **Temperature 0.7 breaks replay determinism.** Stage-2 canonical eval
  is still deterministic (FSM `Solver.move` is greedy); only Stage-1
  author-loop sampling uses 0.7.

### Reverting

`BenchConfig` is a value object; future cycles can lower defaults for
smoke runs. Publication must report the config used.

## Alternatives considered

### A. Lower defaults for faster cycle time

`max_iters=50, n_trials=1, T=0.0` for sub-minute runs. **Rejected**:
defeats the bench's purpose — tiny budgets don't surface
comprehensiveness.

### B. Higher trials (`n_trials=30`)

**Rejected**: 10 gives σ/√10 ≈ 0.32 σ; cost scales linearly.

### C. Deterministic greedy decoding (`temperature=0.0`)

**Rejected**: T=0 gets stuck on wrong FSM templates; T=0.7 explores.

### D. Separate Stage-1 vs Stage-2 temperature

**Accepted implicitly** — Stage-2 FSM `move()` is greedy by
construction; temperature only affects Stage-1 `_call_model`.

## Implementation pointers

- `src/reward_bench/entities/bench_config.py` — `BenchConfig` frozen dataclass.
- `src/reward_bench/use_cases/run_bench.py` — multi-trial use case.
- `src/reward_bench/frameworks/main.py` — consumes `BenchConfig`.
- `src/tier1/agent_loop.py` — `_call_model` accepts `temperature`,
  `max_tokens`; `run_loop` accepts `max_iters`, `max_no_improve`,
  `finish_floor`.

## Cross-references

- [SPEC.md §"Author-stage inference context"](../../SPEC.md)
- [Lab ADR 0001](0001-condenser-uses-same-model-as-bench.md) — same-model condenser.
- [Lab ADR 0002](0002-main-emits-sentinel-on-malformed-submission.md) — failure-mode handling.
- `_bak/bin/campaign_tier1.sh` — source of truth for legacy settings.
