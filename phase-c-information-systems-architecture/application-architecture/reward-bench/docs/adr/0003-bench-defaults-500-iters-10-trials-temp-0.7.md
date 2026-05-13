# ADR 0003 — Bench defaults: 500 iters, 10 trials, temperature 0.7, 128 K context, same-model condenser

## Status

Accepted (2026-05-13). Active.

## Context

The cycle-12 end-to-end run for `qwen3.6-27b-awq` produced
`mean_score=3360.8`. The legacy `_bak/bin/campaign_tier1.sh` campaign
for the same model produced **~15920** (task #8). The 4.7×
gap is not a model difference — it is a **knob-setting** difference.

Gap analysis:

| Lever | `_bak` | minimum-viable rewrite (cycles 11-15) | Approx. factor |
| ----- | ------ | ------------------------------------- | -------------- |
| `max_iters` (turns per attempt) | **500** | 30 | 16× turn budget |
| `n_trials` (attempts per model) | **10** | 1 | 1.5-2× lift on reported mean |
| `temperature` | **0.7** | 0.0 (greedy) | 1.2-1.5× from exploration |
| Condenser | llama-3.1-8b on the 5090 | none (only the seam, cycle 15) | enables higher `max_iters` |
| `max_no_improve` (no-improve guard) | 999999 (never trigger) | n/a | forces the loop to keep iterating |
| `finish_floor` (reject low-scoring finish) | 0 (any score accepted) | n/a | shape-only enforcement |

Product of those factors lands ≈ 5-9×, matching the observed 4.7×
gap to within an order of magnitude. The new tree is producing 21 %
of the legacy's score because it is running 21 % of the legacy's
work per attempt with 10 % of the trials.

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

These are the bench defaults — what every leaderboard publication
must report under unless explicitly overridden. They land as fields
on a `BenchConfig` value object.

## Consequences

### Positive

- **Closes the score-quality gap.** Re-running `qwen3.6-27b-awq` under
  these defaults targets the `_bak` 15.9 k baseline (queued task #8).
- **Surfaces real model quality differences.** A smarter model gets
  more from 500 iters + 10 trials + exploration temperature than from
  30 iters + 1 trial + greedy decoding. The high-iter setup is what
  makes the leaderboard discriminate.
- **One source of truth.** All four call sites (`main()`,
  `agent_loop._call_model`, the multi-trial use case, the condenser
  trigger) read from `BenchConfig` instead of hardcoding their own
  numbers.
- **Cross-model A/B becomes clean.** Every model runs under identical
  defaults; differences in mean_score reflect model capability, not
  knob drift.

### Negative

- **Wall time.** 500 iters × 10 trials × ~2 s per turn × 21 active
  models ≈ 30+ GPU-hours per full leaderboard run on Blackwell. The
  bench is no longer "click and watch in 60 seconds" — it's a
  campaign.
- **Condenser blocking.** `max_iters=500` blows past the 128 K
  budget on a single conversation. The condenser must work
  reliably before this default is safe — cycles 16-17 unblock it.
  Until then, `BenchConfig` defaults can ship but the actual long
  runs must wait for the condenser.
- **Temperature 0.7 breaks replay determinism.** SPEC.md tier 1
  requires 0 % replay tolerance. Stage-2 canonical eval still
  runs deterministically (the FSM `Solver.move` is greedy); only
  Stage-1 author-loop sampling uses 0.7.

### Reverting

`BenchConfig` is a value object; a future cycle can lower defaults
(e.g. `max_iters=50, n_trials=3`) for fast smoke runs. The leaderboard
publication must report the config used; readers compare across
identical configs.

## Alternatives considered

### A. Lower defaults for faster cycle time

`max_iters=50, n_trials=1, temperature=0.0` keeps an end-to-end run
under a minute. **Rejected** because it defeats the bench's purpose
— `reward-bench` is the comprehensiveness scoreboard; tiny budgets
do not surface comprehensiveness.

### B. Higher trials (`n_trials=30`)

Tighter confidence intervals on the mean. **Rejected** because 10
already gives σ/√10 ≈ 0.32 σ which is usable; cost scales linearly
in trials.

### C. Deterministic greedy decoding (`temperature=0.0`)

Replay-determinism friendly. **Rejected** because the author loop
benefits from exploration: when the FSM template is wrong, T=0 gets
stuck on the wrong template; T=0.7 finds alternatives.

### D. Separate Stage-1 temperature vs Stage-2 temperature

Stage-1 (author loop) sampling with T=0.7; Stage-2 (canonical eval,
deterministic FSM) with no model in the loop. **Accepted implicitly**
— the FSM's `move()` is greedy by construction; temperature only
affects the author loop's `_call_model` calls.

## Implementation pointers

- **`src/reward_bench/entities/bench_config.py`** — `BenchConfig`
  frozen dataclass with the seven fields above. Cycle 16.
- **`src/reward_bench/use_cases/run_bench.py`** — multi-trial use
  case that calls `main()` N times and aggregates. Cycle 19 or 20.
- **`src/reward_bench/frameworks/main.py`** — consumes `BenchConfig`
  (`max_iters`, `temperature` propagate to `agent_loop.run_loop` and
  `_call_model`). Cycle 17.
- **`src/tier1/agent_loop.py`** — `_call_model` signature accepts
  `temperature` and `max_tokens`; `run_loop` accepts `max_iters`,
  `max_no_improve`, `finish_floor` (the last two also force
  agent_loop behavior). Cycles 17 + 21.
- **`reward-bench/docs/adr/0001-condenser-uses-same-model-as-bench.md`**
  — the condenser-model decision that makes `max_iters=500` viable.
- **`reward-bench/docs/adr/0002-main-emits-sentinel-on-malformed-submission.md`**
  — the sentinel pattern still applies under the new defaults.

## Cross-references

- [SPEC.md §"Author-stage inference context"](../../SPEC.md)
- [Lab ADR 0001](0001-condenser-uses-same-model-as-bench.md) — same-model
  condenser; the rationale that lets us raise `max_iters` without a
  second GPU.
- [Lab ADR 0002](0002-main-emits-sentinel-on-malformed-submission.md) —
  failure-mode handling.
- `_bak/bin/campaign_tier1.sh` — the source-of-truth document for the
  legacy settings.
- Task #8 — Verify Qwen3.6-27B-AWQ still scores ~15.9k with patched
  agent_loop.
