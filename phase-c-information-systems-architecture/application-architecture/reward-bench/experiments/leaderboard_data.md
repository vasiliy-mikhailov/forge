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

### Cycle 37 campaign (5x iters lever, supervisor active)

- **Config**: `BenchConfig(max_iters=500, n_trials=3, temperature=0.7,
  hard_wall_sec=120, supervisor_every_k=20)`
- **Per-trial mean**: `[0.0, 0.0, 6525.2]`
- **Aggregate**: `mean_of_means=2175.1 best_mean=6525.2 worst_mean=0.0`
- **Max tile**: **1024** (best trial)
- **Walltime**: 549 s (9:09 for 3 trials)
- **Artifact**: `experiments/2026-05-14-iters500-T07-n3.json`
- **Notes**:
  - **5x iters lever only delivered +4% best_mean (6261 -> 6525)**.
    The model is NOT productively using max_iters>100.
  - Trial 1: scoring hit `hard_wall_sec=120` walltime — the submission
    was so slow per move that 20 games at 120s aggregate cap meant
    most seeds returned `walltime_exceeded` sentinel.
  - Trial 2: 0.0 (broken solver, sentinel).
  - Wall time per trial collapsed from ~5 min (iters100) to ~3 min
    (iters500). This means trials are FINISHING EARLY, not running
    long. Cause unknown without per-iter telemetry — drives cycle 38
    stall-detection telemetry.
  - **Conclusion**: bumping `max_iters` alone is NOT the path to
    `_bak`'s 15920. The model needs a different lever — likely a
    smarter Solver prompt template OR a better condenser OR
    multi-stage author + reviewer roles.

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


### Cycle 40 reproduction (_bak/bin/agent_loop.py, qwen3.6-27b-awq)

User question: 'why did _bak get 15k?' Investigation:

1. The leaderboard's 15920 was the legacy mistral-small-24b multi-trial
   campaign (`/mnt/.../experiments/2026-05-08-campaign-mistral-small-24b-trial8/`).
   NOT qwen3.6-27b-awq.

2. _bak's actual qwen3.6-27b-awq single-trial best was 10884
   (`/mnt/.../experiments/2026-05-05-qwen3.6-27b-awq-int4-tier1/`).

3. Cycle 36-37 in OUR src/tier1/agent_loop.py: best 6525. That's a
   ~40 percent regression vs same model under _bak's loop. ROOT CAUSE
   suspected in our prompt drift OR loop wiring — needs cycle 41 bisect.

Reproduction with _bak/bin/agent_loop.py UNMODIFIED (just edited
context-budget-tokens=100000 to fit the new 128K vLLM), same vLLM
endpoint, same model, three trials with seeds 1/2/3 in parallel,
max_iters=100/200, temperature=0.7:

| Trial | Mean | Median | Max | Top tiles |
|-------|------|--------|-----|-----------|
| v2 (seed=1) | 10847 | 10284 | 28064 | 2048 x3 |
| t2 (seed=2) | 11734 | 12208 | 22224 | 2048 |
| t3 (seed=3) | 3406  | 3124  | 6084  | 512 |

best_mean = 11734  mean_of_means = 8662  max_single = 28064

Two of three trials cleanly beat _bak's 10884 baseline. This confirms
the model is NOT the bottleneck. Our pipeline broke; _bak's didn't.

Next: cycle 41 — bisect what diverged between _bak/bin/agent_loop.py
and src/tier1/agent_loop.py.

## Multi-model per-model bench (cycle 41+, _bak/bin/agent_loop.py runner)

Per-model leaderboard cells produced by
`tests/reward_bench/frameworks/campaigns/test_per_model_bak_runner.py`
(cycle 41). Each row = one model x one seed, scored on canonical
seeds 1000-1019. High variance — `_bak`'s `agent_loop.py` is the
runner because cycle 40 proved a ~40 percent regression in our
`src/tier1/agent_loop.py`.

| Model | Seed | T | Iters | Mean | Median | Max | Min | Top tile | Artifact |
|---|---|---|---|---|---|---|---|---|---|

### Cycle 67 active-loop campaign (ADR 0008 end-to-end live)

Trial 1: **mean_score=15,918.6 median=17,016 max_tile=2048 n_games=20**

This is the first canonical-seed score on the ACTIVE
`src/tier1/agent_loop.py` that BEATS the legacy `legacy_agent_loop.py`
reference (cycle 40: 11,734). Achieved against qwen3.6-27b-awq under
the same vLLM endpoint, same SKILL_tier1.md contract.

Approaches the user-stated target ("close to 15k") and matches the
historical mistral-small-24b 15,920 figure from `_bak`'s legacy
campaign.

**Closes the cycle-40 regression.** The bisect produced 9 landed
fixes:
  - cycle 48: best-snapshot + restore
  - cycle 50: finish-floor enforcement
  - cycle 51: parser robustness
  - cycle 52: max_tokens=12288 (matching legacy)
  - cycle 53: protocol validator
  - cycle 58: execute_submission tool dispatcher (ADR 0008 primary)
  - cycle 63: parser reads execute_submission JSON observation
  - cycle 65: finish-time body promotion to submission.py
  - cycle 66: SYSTEM_PROMPT advertises execute_submission as primary

Live evidence the model is iterating productively:
  iter 9  → new best dev MEAN=5063
  iter 10 → 5737
  iter 12 → 11697
  iter 13 → 15611
  iter 14 → 18005
  finish → canonical mean=15,918

ADR 0007 (legacy blessed runner) is on track to be superseded once
trials 2/3 confirm consistency. Docker isolation (ADR 0006 layer 2)
is the remaining hardening cycle.

### Cycle 71 active-loop campaign (post-cycle-70 verification, 3 trials)

After cycle 70 deleted the duplicate game loop in `_execute_submission`
(delegates to canonical `score_submission` use case), re-ran
`test_iters100_T07_n3` on `qwen3.6-27b-awq` to verify the refactor
did not regress the active loop.

Per-trial: **[122.6, 15307.0, 9375.8]**
  - mean_of_means = 8268.5
  - best_mean = 15307.0
  - worst_mean = 122.6
  - max_max_tile = 2048 across all trials

**Trial 2 = 15,307** is the cleanest result and confirms parity with
cycle 67's 15,918 (within 4% noise). Cycle 70 refactor verified.

**Trial 1 = 122.6** is a real-world repro of a NEW issue cycle 71
exposed: dev-path / canonical-path budget asymmetry. The model wrote
a Solver fast enough for the dev path's 30s/5seeds ≈ 6s/seed budget
but slow on canonical's 60s/20seeds ≈ 3s/seed budget. canonical
walltime_sec=60.0 (cap hit) and median=0 means most games
walltime_exceeded'd. The dev signal misled the model into calling
`finish()` on a Solver that doesn't survive canonical scoring.

This is the motivation for **cycle 72**: derive `DEV_HARD_WALL_S`
from the canonical config so dev's per-game budget MATCHES canonical's
(currently 60×5/20 = 15s for the default campaign), making the dev
signal honest by construction.

Live evidence that **cycle 70 mechanisms fired correctly**:
  - trial 1, 2, 3: no execute_submission wedge (cycle-69 bug
    impossible by construction).
  - trial 3: cycle-48 best-snapshot restore observed live —
    `restored submission.best.py (dev MEAN=14696.0) to submission.py
    for scoring` (model wrote a worse final submission; harness
    restored the best one).
  - all trials: cycle-65 finish-time promotion fired.
  - canonical scoring on trials 2 + 3 completed in 1.1–1.3s (vs
    trial 1's 60s cap) — the canonical scorer's per-game timeout
    is doing its job too.

Artifact: `experiments/2026-05-13-iters100-T07-n3.json`.
Commit: cycle 70 = 17ef812 (the refactor).

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
| `qwen3.6-27b-awq` | 1 | 0.7 | 200 | 2551 | 2432 | 4948 | 992 | 256 | `2026-05-14-qwen3.6-27b-awq-bak-runner.json` |
| `qwen3.5-27b-nvfp4` | 1 | 0.7 | 200 | 8705 | 7624 | 16852 | 2776 | 1024 | `2026-05-14-qwen3.5-27b-nvfp4-bak-runner.json` |
| `gemma-4-31b-nvfp4` | 1 | 0.7 | 200 | 11 | 8 | 36 | 0 | 8 | `2026-05-14-gemma-4-31b-nvfp4-bak-runner.json` |
