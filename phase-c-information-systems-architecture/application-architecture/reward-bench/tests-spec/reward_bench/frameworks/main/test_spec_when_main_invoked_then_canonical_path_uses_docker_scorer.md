# `test_spec_when_main_invoked_then_canonical_path_uses_docker_scorer`

Pins the **`main()` → `DockerCanonicalScorer`** wiring per the
[ADR 0006 Layer 2 amendment](../../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md).

## Why

Cycle 105 sub-A landed the parallel runner inside the container; sub-B
landed the `DockerCanonicalScorer` adapter that spawns it. Sub-C is
the wiring: `main()`'s canonical scoring step (today: in-process
`score_submission`) switches to `DockerCanonicalScorer.score(...)`.

After sub-C the only path through `main()` for canonical scoring is
the Docker one. The in-process `score_submission` use-case stays in
the codebase for tests that need an in-memory scorer (it's also
referenced by `_execute_submission` for the dev path — cycle 106
will move that to Docker too).

## Contract

`main(model_id, seeds=..., config=..., canonical_scorer=None)`:

- `canonical_scorer` is an injection point (cycle 99/ADR 0014 DI
  pattern). When `None`, `main()` constructs a default
  `DockerCanonicalScorer()` (50 % of host cores, default image).
- The canonical scoring call becomes
  `result = canonical_scorer.score(submission_path, seeds,
   hard_wall_sec=config.hard_wall_sec, reports_root=<workspace>/reports)`.
- Pre-sub-C in-process call to `score_submission(SolverCls, seeds, ...)`
  is removed.
- All other behaviour (`_pick_model`, `ensure_serving_model`, run_loop,
  best-snapshot restore, sentinel-on-malformed) is unchanged.

## Model client injection point

- **Seam**: `main(canonical_scorer=...)`.
- **Default**: when `None`, production binds `DockerCanonicalScorer()`.
  Live tests pass nothing (use production); fast/unit tests inject a
  recorder that returns a synthetic `AttemptResult` so they run
  offline.
- **Live override**: explicit `canonical_scorer=DockerCanonicalScorer()`
  for tests that want to validate the actual Docker spawn end-to-end.

## Tests

### `test_when_main_invoked_with_canonical_scorer_then_scorer_score_called`

- **Arrange**: `RecordingScorer` whose `score(...)` captures arguments
  and returns a fixed `AttemptResult`. Stub `run_loop` to terminate
  early (one-iter sentinel path or finish-immediately).
- **Act**: `main(model_id='qwen3.6-27b-awq', config=fast_cfg,
  canonical_scorer=recorder)`.
- **Assert**: `recorder.calls` has exactly one entry. The
  `submission_path` argument points at `<workspace>/submission.py`.
  `seeds` argument matches the `seeds` passed to `main`.
  `hard_wall_sec` argument matches `config.hard_wall_sec`.

### `test_when_main_default_canonical_scorer_is_docker_canonical_scorer`

- **Arrange**: inspect the default factory; we don't actually invoke
  it (no Docker available in the fast gate).
- **Act**: read `main()`'s signature or factory default.
- **Assert**: when `canonical_scorer is None`, `main()` builds a
  `DockerCanonicalScorer` instance.

### `test_when_canonical_scorer_returns_attempt_result_then_main_returns_it_unchanged`

- **Arrange**: recorder returns an `AttemptResult` with `mean_score=1234.5`.
- **Act**: `main(...)`.
- **Assert**: returned `AttemptResult.mean_score == 1234.5` (i.e.
  `main()` doesn't post-process the scorer's result; the scorer IS
  the canonical source of truth).

Test code: [`tests/reward_bench/frameworks/test_main_docker_scorer.py`](../../../../tests/reward_bench/frameworks/test_main_docker_scorer.py).

## Runtime scope

> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.

