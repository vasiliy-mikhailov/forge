# `test_when_main_invoked_with_qwen3_6_27b_awq_then_solver_class_scored_20_games`

Pins the **happy-path contract** for the bench end-to-end run: when
`main()` runs against the live `qwen3.6-27b-awq` model with the
test-friendly config, the model produces a valid `class Solver` and
`score_submission` plays all 20 canonical seeds.

This is the cycle-12 strict contract; sentinel `n_games=0` is NOT
acceptable here. The cycle-11 shape-only test
([`test_spec_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted`](test_spec_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted.md))
DOES accept sentinel.

- **Arrange**: import `AttemptResult`, `BenchConfig`, and `main`.
  Build `_FAST = BenchConfig(max_iters=60, n_trials=1,
  temperature=0.0)` — ADR 0003 defaults (500 iters / T=0.7) would
  take minutes. Cycle 99b bumped from 30 to 60 after cycle-99a
  live run showed qwen3.6-27b-awq at temp=0.0 needs ~30+ iters
  before finish. vLLM container serving `qwen3.6-27b-awq`.
- **Act**: `result = main(model_id='qwen3.6-27b-awq', config=_FAST)`.
- **Assert**:
  - `isinstance(result, AttemptResult)`.
  - `result.n_games == 20` (no sentinel — model produced a valid
    Solver class).
  - `len(result.games) == 20`.
  - No game has `final_state in {'solver_error', 'invalid_action'}`.
    Cycle 99b broadened from the cycle-12 wording (`in {'won', 'lost'}`)
    to admit cycle-78 `stagnated` and cycle-23/27 `walltime_exceeded` —
    both are legitimate game terminals (the Solver ran without
    crashing). The intent of this assertion is reject Solver crashes
    only.
  - `result.mean_score >= 0.0`.

Real-system observation from cycle 11: qwen3.6-27b-awq under the
prior weaker `FIRST_USER` consistently wrote `def solve(state)` with
int actions instead of `class Solver` with WASD strings. Cycle 12
strengthened `FIRST_USER` to make the model converge.

Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.

