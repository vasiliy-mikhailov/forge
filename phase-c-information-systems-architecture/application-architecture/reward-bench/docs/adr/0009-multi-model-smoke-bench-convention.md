# ADR 0009 v3: Multi-model smoke bench convention

## Status

Accepted v1 (cycle 72) — max_iters=10, asserted on canonical mean.
Superseded by v2 (cycle 76) — max_iters=100 + smoke_early_stop on first dev_mean > 0.
Superseded by v3 (cycle 79 + 80) — smoke success criterion = best_dev_mean > 0
(not canonical); canonical-skip in smoke mode for speed.

## Context

`MODEL_REGISTRY` has 22 candidate models. Cycle 72 v1 of this ADR
used `SMOKE_CONFIG = BenchConfig(max_iters=10, n_trials=1, …)` —
~5 min/model, ~2.5 h total. v1 surfaced two real bugs (cycle 73
and cycle 74 model-id wiring), and produced 6 PASS / 16 FAIL/ERROR.

User-flagged result analysis (post v1): the v1 cap of 10 iters was
biased toward fast-starters. `qwen3.6-27b-awq` — the bench's
strongest model at full config (cycle 67: 15,918; cycle 71 trial 2:
15,307) — smoke-FAILed v1 with `0.0`. Cycle 71 trajectories show
that model emits its FIRST `execute_submission` consistently at
iter 11-14. With `max_iters=10` it never even produces a single
submission; v1 scored zero. So a v1 "FAIL" really meant *"did not
produce a first solution within 10 iters"*, not *"cannot solve the
task"*.

## Decision (v2)

**Smoke convention is rewritten as**:

`SMOKE_CONFIG = BenchConfig(`
  `max_iters=100,         # was 10 — give slow-starters a chance`
  `n_trials=1,            # unchanged`
  `temperature=0.7,       # unchanged`
  `finish_floor=0.0,      # unchanged — model can finish() any time`
  `hard_wall_sec=60.0,    # unchanged — same canonical cap`
  `supervisor_every_k=0,  # unchanged`
  `smoke_early_stop=True, # NEW — bench forces finished=True on first dev_mean > 0`
`)`

The new `smoke_early_stop` flag (cycle 76) lives on `BenchConfig`
and is wired through `main()` to `run_loop()`. When set, the loop
forces `finished=True` as soon as ANY `execute_submission`
observation produces `dev_mean > 0`. The cycle-48 best-snapshot
machinery then restores the high-water-mark submission for
canonical scoring. Compute saving: cycle 71 trial 2 would exit at
iter 14 (first positive dev) instead of iter 74 — ~80% reduction.

Each model in `MODEL_REGISTRY` still has its own test_spec under
`tests-spec/reward_bench/frameworks/smoke/`, pinning the v2
`SMOKE_CONFIG` and asserting `result.mean_score > 0` for that
specific model.

## "0.0 is a bug" thesis

With v2's 100-iter cap and early-stop, if a model still cannot
achieve `canonical_mean > 0`, **the failure is a real bug**, not
a verdict on the model's reasoning ability. Candidate root causes:

  - Tool-call parser mismatch (model emits tool calls in a format
    the bench's `parse_tool_calls` can't read).
  - Tokenizer issue (model output cut off mid-code).
  - Budget asymmetry (cycle 71 trial 1 / cycle 77 deferred):
    Solver is fine at dev's 30s/5seeds but times out at
    canonical's 60s/20seeds.
  - vLLM payload mismatch (e.g. cycle 74 hardcoded model name).
  - Registry data drift (e.g. cycle 74 max_model_len).

Each smoke FAIL with `canonical_mean == 0` triggers a follow-up
CATS cycle scoped to that model (or that family).

## Decision delta v3 (cycle 79)

v2 asserted `result.mean_score > 0` — the CANONICAL second-stage
score on 20 canonical seeds. v3 changes the smoke success criterion
to `result.best_dev_mean > 0` — the BEST `dev_mean` observed by any
`execute_submission` observation during the agent loop.

Rationale (user, cycle 79): smoke's question is *"did the model
produce ANY working code?"*. That signal lives in `dev_mean` from
`execute_submission`. Canonical scoring is the next-stage pipeline
with different seeds and a different per-game budget; under cycle 71
budget asymmetry it can show 0 even when a working solution already
emerged. Pinning smoke on canonical adds a dependency on the
canonical-stage's correctness, which is not what smoke is asking.

Implementation:
  + `AttemptResult.best_dev_mean: Optional[float] = None` (cycle 79).
  + `run_loop` returns its tracked `_best_dev_mean` alongside
    `iterations / messages / finished`.
  + `main()` reads it and `dataclasses.replace`s the
    `AttemptResult` to surface it.
  + Smoke test asserts `(result.best_dev_mean or 0) > 0`. The
    canonical `mean_score` is still recorded in the artifact for
    informational purposes.

Per-model smoke test_specs (regenerated cycle 79) document the
new contract.

### Cycle 80 optimisation: canonical-skip in smoke mode

Once `smoke_early_stop` fires with `best_dev_mean > 0`, the smoke
contract (v3 above) is already satisfied. The canonical
second-stage scoring (20 games on canonical seeds, up to 60s
budget) is pure overhead in smoke mode. Cycle 80 short-circuits:
when `config.smoke_early_stop` is True and `run_loop` returned a
positive `best_dev_mean`, `main()` returns an `AttemptResult`
carrying just `best_dev_mean` and informational zeros for the
other fields; `score_submission` is not called. Saves 60s+ per
smoke model run.

## Consequences

+ Strong models that need warmup (qwen3.6-27b-awq class) now have
  a fair chance to produce their first solution.
+ Early-stop keeps total bench time bounded — the previously
  proven-strong models exit ~iter 14 instead of grinding to 100.
+ Failed models get clean root-cause attribution: a 0.0 result is
  a triggered investigation cycle, not a closed verdict.
+ Total bench time estimate: 4-6 h for 22 models (high-variance
  because the thinking models still need long per-iter wall time).

## Related

- [ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md)
  full campaign defaults.
- [ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
  hard_wall_sec inheritance.
- [ADR 0008](0008-docker-sandboxed-execute-submission-tool.md)
  execute_submission dispatcher.
