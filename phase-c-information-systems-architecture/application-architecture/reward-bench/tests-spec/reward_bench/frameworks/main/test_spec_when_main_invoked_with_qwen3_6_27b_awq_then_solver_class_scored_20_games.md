# `test_when_main_invoked_with_qwen3_6_27b_awq_then_solver_class_scored_20_games`
Pins the **happy-path contract** for the bench end-to-end run: when
`main()` runs against the live `qwen3.6-27b-awq` model with the
test-friendly config, the model produces a valid `class Solver`,
`score_submission` plays all 20 canonical seeds, AND the mean score
clears the trivial-fallback floor.
This is the strict contract; sentinel `n_games=0` is NOT acceptable
here. The shape-only test
([`test_spec_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted`](test_spec_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted.md))
DOES accept sentinel.
- **Arrange**: import `AttemptResult`, `BenchConfig`, and `main`.
 Build `_FAST = BenchConfig(max_iters=120, n_trials=1,
 temperature=0.7,
  hard_wall_sec=60.0)` — the canonical defaults (500 iters / T=0.7)
 would take minutes; 120 iters is enough for qwen3.6-27b-awq at
 T=0.7 to converge on a non-trivial Solver. vLLM container
 serving `qwen3.6-27b-awq`.
- **Act**: `result = main(model_id='qwen3.6-27b-awq', config=_FAST)`.
- **Assert**:
 - `isinstance(result, AttemptResult)`.
 - `result.n_games == 20` (no sentinel — model produced a valid
 Solver class).
 - `len(result.games) == 20`.
 - No game has `final_state in {'solver_error', 'invalid_action'}`.
 `stagnated` and `walltime_exceeded` are admitted — both are
 legitimate game terminals (the Solver ran without crashing);
 this assertion's intent is to reject Solver crashes only.
 - `result.mean_score >= 32` — quality floor that catches the
 trivial-fallback pathology (`return 'W'` / `return 'S'`).
 Trivial-W scores ~4–20 across 20 seeds; any non-degenerate
 Solver clears 1000+. 32 sits comfortably above trivial-W
 without flagging legitimate-but-weak solvers.
## Why a quality floor
Without a score-quality assertion, a model that emits
`class Solver:\n def move(self, board): return 'W'` PASSES this
test — trivial-W produces real game terminals (won/lost/stagnated)
with non-zero score, so the shape and crash-detection assertions all
pass. The W-fallback then surfaces only in the multi-hour production
canonical campaign, hours after the regression landed. The quality
floor turns the W-fallback into a unit-time regression.
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: live — this test asserts on real-model output quality,
 not DI shape; it must run against the actual vLLM container.
- **Override**: marked `@pytest.mark.live` so default-fake autouse
 yields to the real `VllmOpenAIClient`.
## Runtime scope
> **Runtime scope**: live — exercises real model + real Docker scorer
> end-to-end. Unit-runtime coverage is provided by the sibling test_specs
> in this directory that exercise `main()` via DI seams. Production-runtime
> coverage is the canonical bench campaign.

Test code: [`../../../../tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py)::`test_when_main_invoked_with_qwen3_6_27b_awq_then_solver_class_scored_20_games`.
