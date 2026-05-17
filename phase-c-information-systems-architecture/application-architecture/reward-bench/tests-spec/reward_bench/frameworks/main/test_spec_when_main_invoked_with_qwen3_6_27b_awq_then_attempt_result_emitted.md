# `test_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted`
Pins the composition root's **shape contract**:
`reward_bench.frameworks.main.main()` always returns an
`AttemptResult` — happy path (model produces working `class Solver`,
20 games played) and sad path (model produces wrong-shape submission,
sentinel `AttemptResult(n_games=0, games=())` emitted per
[SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md))
both produce the same return type. The bench never crashes on a
malformed submission.
This cycle's contract is **shape-only**; model quality (mean_score,
solver correctness) is pinned in
[`test_spec_when_main_invoked_with_qwen3_6_27b_awq_then_solver_class_scored_20_games`](test_spec_when_main_invoked_with_qwen3_6_27b_awq_then_solver_class_scored_20_games.md).
- **Arrange**: import `AttemptResult`, `BenchConfig`, and `main`.
 Build `_FAST = BenchConfig(max_iters=30, n_trials=1,
 temperature=0.0)` — test-friendly knobs that bound wall time;
 [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
 defaults (500 iters / T=0.7) would take minutes. vLLM container
 `reward-bench-vllm` serving `qwen3.6-27b-awq` (`ensure_serving`
 brings it up if down).
- **Act**: `result = main(model_id='qwen3.6-27b-awq', config=_FAST)`.
- **Assert**:
 - `isinstance(result, AttemptResult)` — always.
 - `result.n_games == len(result.games)` — invariant.
 - `result.aggregate_walltime_sec >= 0.0`.
 - Either `n_games == 20` AND `mean_score >= 0.0` (happy path) OR
 `n_games == 0` AND `len(games) == 0` (sentinel).
Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.
