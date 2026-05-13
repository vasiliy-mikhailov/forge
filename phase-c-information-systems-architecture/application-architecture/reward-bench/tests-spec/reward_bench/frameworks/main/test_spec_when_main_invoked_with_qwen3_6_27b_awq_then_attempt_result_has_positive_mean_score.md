# `test_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_has_positive_mean_score`

Pins the composition root: `reward_bench.frameworks.main.main()`
runs the bench end-to-end for `qwen3.6-27b-awq` and returns an
`AttemptResult` whose `mean_score` is strictly positive. This is the
first end-to-end CATS test — every entity, registry, and adapter
landed in cycles 1-10 gets exercised by one real run against the
live vLLM container.

- **Arrange**: import `main` from `src.reward_bench.frameworks.main`.
  vLLM container `reward-bench-vllm` is up serving
  `qwen3.6-27b-awq` (the `ensure_serving` call inside `main` will
  health-check it; if it is down `main` brings it up).
- **Act**: `result = main(model_id='qwen3.6-27b-awq')`.
- **Assert**:
  - `result` is an `AttemptResult` instance.
  - `result.n_games == 20` (canonical eval count).
  - `result.mean_score > 0` (any positive mean — the real model
    produces a working FSM that scores above zero on at least one
    of the 20 seeds).
  - `len(result.games) == 20`.
  - `tuple(g.seed for g in result.games) == tuple(range(1000, 1020))`.

This test runs the agent loop against the real model (5-10 min wall
time) and then plays 20 canonical games. It is the bench's
canonical health-check run.

Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
