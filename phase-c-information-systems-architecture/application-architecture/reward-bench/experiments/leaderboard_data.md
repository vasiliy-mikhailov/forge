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

### Cycle 29 campaign (after cycles 27+28+29 sentinels)

- **Config**: `BenchConfig(max_iters=100, n_trials=3, temperature=0.7,
  hard_wall_sec=60.0)`
- **Per-trial mean**: `[5932.4, 0.4, 0.0]`
- **Aggregate**: `mean_of_means=1977.6 best_mean=5932.4 worst_mean=0.0`
- **Max tile**: **1024** (best single game; 2x prior peak of 512)
- **Walltime**: 558 s (9:18 for 3 trials)
- **Artifact**: `experiments/2026-05-13-iters100-T07-n3.json`
- **Notes**:
  - Best single trial **5932.4** — first time clearly above the
    cycle-12-22 plateau (3000-3500). Same trial hit **max_tile=1024**.
  - Trials 2 and 3 collapsed (0.4 and 0.0) because of two real-system
    bugs reproduced live and fixed in the same campaign:
    - Trial 2: `Solver.move()` called undefined transitions trigger
      `to_opening()` -> cycle 28 sentinel.
    - Trial 3: `Solver.__init__()` called undefined transitions trigger
      `start()` -> cycle 29 sentinel.
    + a SyntaxError in trial 3's final submission.py (ADR-0002 sentinel).
  - Mean-of-means (1977.6) is DROP vs cycle-22 (3144.4) because two of
    three trials collapsed. The best-mean lift (5932 vs 3575, +66%) is
    the real signal — the model CAN do significantly better when it
    doesn't break the transitions API.
  - Sentinels did exactly what ADR 0002 + cycle 27/28/29 demand: the
    leaderboard still got a 3-trial data point instead of a no-data
    crash. This is the test-spec-backed artifact rule paying off.

### Cycle 36 campaign (supervisor active, iters100)

- **Config**: `BenchConfig(max_iters=100, n_trials=3, temperature=0.7,
  hard_wall_sec=60.0, supervisor_every_k=10)` — supervisor consults
  LlmSupervisor (ADR 0001+0005) every 10 iters and forces a finish on
  stop_recommended.
- **Per-trial mean**: `[3809.0, 0.0, 6261.0]`
- **Aggregate**: `mean_of_means=3356.7 best_mean=6261.0 worst_mean=0.0`
- **Max tile**: **1024** (best trial)
- **Walltime**: 583 s (9:42 for 3 trials)
- **Artifact**: `experiments/2026-05-13-iters100-T07-n3.json`
- **Notes**:
  - **best_mean lift: 5932 -> 6261 (+5.5%)** with supervisor wired.
    First trial saw a clear improvement; trial 3 even higher.
  - Trial 2 SyntaxError sentinel (ADR 0002) again — submission was
    invalid Python. Supervisor doesn't help submissions that don't
    parse.
  - Walltime is +5% over cycle-29 (583 vs 558 s) — supervisor adds
    ~10 LLM calls per 100 iters. Net cost trivial.
  - Plateau-stop never fired in this run (no trial finished early via
    the supervisor) — at max_iters=100 the model is still climbing
    when iters run out, not plateauing.


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
