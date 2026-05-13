# `test_when_run_bench_trials_called_with_n_trials_three_then_returns_tuple_of_three_attempt_results`

Pins the multi-trial use case: `run_bench_trials(model_id, config,
runner)` invokes `runner(model_id=..., config=...)` exactly
`config.n_trials` times and returns the resulting `AttemptResult`s
as a tuple.

The `runner` parameter is injectable so the unit test substitutes a
stub for `main()`; the wiring layer defaults to the real
`main()` for production use.

Per [ADR 0003](../../../../docs/adr/0003-bench-defaults-500-iters-10-trials-temp-0.7.md),
`n_trials=10` is the default; tests use small values to bound
walltime.

- **Arrange**: import `run_bench_trials`, `BenchConfig`,
  `AttemptResult`. Build a stub runner that increments a counter
  and returns a distinct `AttemptResult(mean_score=float(i), ...)`
  for each call. `config = BenchConfig(max_iters=1, n_trials=3,
  temperature=0.0)`.
- **Act**: `trials = run_bench_trials(model_id='stub',
  config=config, runner=stub_runner)`.
- **Assert**:
  - `isinstance(trials, tuple)`.
  - `len(trials) == 3`.
  - The stub was invoked exactly 3 times.
  - Each invocation received `model_id='stub'` and the same
    `config` instance.

Test code: [`tests/reward_bench/use_cases/test_run_bench_trials.py`](../../../../tests/reward_bench/use_cases/test_run_bench_trials.py).
