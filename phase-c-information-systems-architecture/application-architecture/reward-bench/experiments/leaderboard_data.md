# Leaderboard data points

Append-only record of every meaningful bench run. Each entry is one
config × model cell.

## 2026-05-13 — qwen3.6-27b-awq

### Cycle 12 strict (deterministic baseline)

- **Config**: `BenchConfig(max_iters=30, n_trials=1, temperature=0.0)`
- **Result**: `mean_score=3360.8 median=3004.0 max_tile=512 n_games=20`
- **Walltime**: 56 s end-to-end
- **Notes**: First end-to-end run with a working `class Solver` from
  the live model.

### Cycle 20 (aggressive condenser)

- **Config**: same as cycle 12, but condenser fires every iter past
  `keep_recent=8` (pre-cycle-21 LlmCondenser, no token gate).
- **Result**: `mean_score=3410.0 median=3468.0 max_tile=512 n_games=20`
- **Walltime**: 561 s (10× regression)
- **Notes**: Same quality as cycle 12; the 10× walltime was the
  ADR-0004 driver to make the condenser token-aware.

### Cycle 21 verify (token-aware condenser, baseline restored)

- **Config**: same as cycle 12. ADR 0004 trigger at 80K tokens.
- **Result**: `mean_score=3360.8 median=3004.0 max_tile=512 n_games=20`
- **Walltime**: 55 s
- **Notes**: Identical result to cycle 12 — short conversations
  stay below trigger; condenser plumbing is inactive at this
  `max_iters`.

### Cycle 22 campaign (first multi-trial, T=0.7)

- **Config**: `BenchConfig(max_iters=100, n_trials=3, temperature=0.7)`
- **Per-trial mean**: `[3419.0, 2439.0, 3575.2]`
- **Aggregate**: `mean_of_means=3144.4 best_mean=3575.2 worst_mean=2439.0`
- **Max tile**: 512 (across all trials)
- **Walltime**: 386 s (6:26 for 3 trials)
- **Notes**:
  - Did NOT move us toward `_bak`'s 15920.
  - Mean dropped vs cycle 12 (3360→3144) because of T=0.7 variance.
  - Best single trial (3575) marginal (+6%) over deterministic.
  - One trial regressed badly to 2439.
  - Suggests qwen3.6-27b-awq has a plateau ~3000-3500 at our prompts
    that bigger budgets do not break.

## Reference baselines

### `tasks/2048/baselines/reference_fsm.py` (hand-written)

- **mean_score**: ~7211 across canonical seeds 1000..1019
- **Notes**: The hand-written FSM ceiling. Any model below this is
  "worse than not having the model at all".

### `_bak` (legacy campaign, 2026-04, archived)

- **Config**: `max_iters=500 n_trials=10 temperature=0.7
  condenser=llama-3.1-8b-on-5090`
- **mean_score**: ~15920
- **Notes**: Task #8 baseline target. Not reproducible until cycles
  21-26 land (token-aware condenser, supervisor, larger campaigns).

## Gap to reproduce `_bak` 15.9k

| Lever | `_bak` | this session's max | factor missing |
| ----- | ------ | ------------------ | -------------- |
| `max_iters` | 500 | 100 | 5× |
| `n_trials` | 10 | 3 | 3.3× |
| supervisor (ADR 0005) | implicit via finish-floor / max-no-improve | none yet | tasks #2-#5 queued |

Knob tuning alone may NOT close the gap. Cycle-22 data suggests the
model plateaus around 3000-3500; supervisor + better prompts +
restart-on-plateau may be required.
