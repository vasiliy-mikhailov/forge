# `test_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted`

Pins the composition root's **shape contract**:
`reward_bench.frameworks.main.main()` always returns an
`AttemptResult` — happy path (model produces working `class Solver`,
20 games played) and sad path (model produces wrong-shape submission,
sentinel `AttemptResult(n_games=0, games=())` emitted) both produce
the same return type. The bench never crashes on a malformed
submission.

This cycle's contract is **shape-only**; model quality (mean_score,
solver correctness) is a separate cycle's concern.

- **Arrange**: import `AttemptResult` and `main`. vLLM container
  `reward-bench-vllm` serving `qwen3.6-27b-awq` (`ensure_serving`
  brings it up if down).
- **Act**: `result = main(model_id='qwen3.6-27b-awq')`.
- **Assert**:
  - `isinstance(result, AttemptResult)` — always.
  - `result.n_games == len(result.games)` — invariant the
    constructing use case must preserve.
  - `result.aggregate_walltime_sec >= 0.0` — non-negative.
  - Either `n_games == 20` AND `result.mean_score >= 0.0` (happy
    path), OR `n_games == 0` AND `len(result.games) == 0` (sentinel
    for "submission shape error" — model produced a non-Solver
    submission).

Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
