# ADR 0009: Multi-model smoke bench convention

## Status

Accepted (cycle 72).

## Context

The `MODEL_REGISTRY` currently lists 22 candidate models across three
VRAM tiers. The full campaign config (max_iters=100, n_trials=3,
~50 min/model) is too expensive to run against all 22 just to learn
"does this model produce any working submission at all?" The cost is
18+ hours, dominated by models that may fail trivially (parser
mismatch, OOM, protocol violation, slow Solver).

We want a fast quality screen: per model, in ~5–15 minutes wall, does
the bench's ralph loop produce a submission whose **canonical mean
score is strictly positive** (i.e. the model can write code that
actually plays 2048 above zero)?

## Decision

The bench grows a new minimum-effort convention called **smoke**.

A **smoke run** is parameterised by `SMOKE_CONFIG = BenchConfig(`
  `max_iters=10, n_trials=1, temperature=0.7, finish_floor=0.0,`
  `hard_wall_sec=60.0, supervisor_every_k=0)`. Rationale per knob:
  - `max_iters=10` — short enough to bound wall time at ~5 min/model
    of agent loop, long enough that any working model emits at least
    one successful `execute_submission`.
  - `n_trials=1` — variance characterisation is the full campaign's
    job, not smoke's.
  - `finish_floor=0.0` — model may `finish()` as soon as it has any
    positive dev_mean. We are screening for "can do this at all", not
    for the reference baseline.
  - `hard_wall_sec=60.0` — same canonical cap as the full campaign,
    so the smoke result composes with the full campaign result for
    the models that smoke-pass.

Each model in `MODEL_REGISTRY` gets:
  - One test_spec under `tests-spec/reward_bench/frameworks/smoke/`
    named `test_spec_when_smoke_bench_runs_on_<model_id>_then_canonical_mean_above_zero.md`.
    It pins the smoke contract for that specific model. Per CATS,
    every behaviour that distinguishes one model from another is
    named and asserted — not lumped into "models are checked".
  - One parametrised test invocation under
    `tests/reward_bench/frameworks/smoke/test_smoke_all_models.py`.
    It calls `ensure_serving_model(target)` to swap the vLLM
    container, runs `main(model_id, config=SMOKE_CONFIG)`, writes
    the artifact to `experiments/2026-05-14-smoke-<model_id>.json`,
    and asserts `result.mean_score > 0`.

A model failing its smoke is **not** treated as a bench
correctness bug — the bench is reporting truth ("this model
cannot do 2048 inside the smoke budget"). The test_spec records
the failure reason in the leaderboard for that model. Acceptable
failure modes per ADR 0002 sentinel pattern:
  - `protocol_invalid` — model never produced a Solver class.
  - `walltime_exceeded` — Solver was so slow that canonical
    scoring hit the 60s cap and every game sentinel'd.
  - container down — vLLM couldn't bring the model up (OOM,
    bad HF path, parser mismatch). Marked `xfail` for now;
    a real test_spec needs a real ModelTarget in the registry.

## Consequences

+ 22 fast datapoints in ~3 hours of wall (vs ~18 h for full
  campaign).
+ The smoke artifacts double as a screen for the full campaign:
  run full campaign only on models that smoke-pass.
+ The smoke convention exposes per-model pathologies (slow Solver,
  bad parser, etc.) faster than the full campaign would.
+ Cycle 73 (defer): the dev/canonical budget asymmetry exposed by
  cycle 71 trial 1 may bite again here. A model whose Solver is
  borderline-slow will smoke-pass on dev but smoke-FAIL on
  canonical. That is actually GOOD signal for the smoke: it tells
  us this model needs cycle 73's fix to be honestly screened.

## Related

- [ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) — full
  campaign defaults (smoke is the cheaper sibling, not a replacement).
- [ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md) —
  smoke inherits `hard_wall_sec` from the canonical scorer.
- [ADR 0008](0008-docker-sandboxed-execute-submission-tool.md) — smoke
  runs through the ADR 0008 dispatcher (cycle 70 refactor).
