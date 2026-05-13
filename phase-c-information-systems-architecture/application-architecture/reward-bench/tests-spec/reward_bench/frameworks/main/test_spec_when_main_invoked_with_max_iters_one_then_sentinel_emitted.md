# `test_when_main_invoked_with_max_iters_one_then_sentinel_emitted`

Pins that `main()` consumes `BenchConfig.max_iters`. When called with
`BenchConfig(max_iters=1)`, the agent loop runs at most one turn —
not enough for the model to write a valid Solver — so `main()`
returns a sentinel `AttemptResult` (`n_games == 0`).

Stricter than the cycle-11 shape-only contract because we DELIBERATELY
choke the loop to verify the knob propagates. Also serves as the
**fastest end-to-end live-model test** for the bench (one inference
call, finishes in ~10 s).

- **Arrange**: import `main` and `BenchConfig`.
- **Act**: `result = main(model_id='qwen3.6-27b-awq',
  config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0))`.
- **Assert**:
  - `isinstance(result, AttemptResult)`.
  - `result.n_games == 0` (sentinel — too few turns to produce
    a working Solver).

Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
