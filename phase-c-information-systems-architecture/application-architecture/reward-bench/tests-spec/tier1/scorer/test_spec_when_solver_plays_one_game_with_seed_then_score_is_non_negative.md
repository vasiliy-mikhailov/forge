# `test_when_solver_plays_one_game_with_seed_then_score_is_non_negative`
Pins scoring layer: a `Solver` instance, given a seed, plays one 2048
game to terminal and produces a non-negative score.
- **Arrange**: load `tasks/2048/baselines/reference_fsm.py` via
 `src.tier1.harness.load_submission`; instantiate its `Solver`.
- **Act**: `src.tier1.scorer.score_one_game(solver, seed=42)`.
- **Assert**: returns an `int >= 0`.
Test code: [`tests/tier1/test_scorer.py`](../../tests/tier1/test_scorer.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — AttemptResult shape / replay-equality contract; pure-Python; scale-invariant.

Test code: [`../../../tests/tier1/test_scorer.py`](../../../tests/tier1/test_scorer.py)::`test_when_solver_plays_one_game_with_seed_then_score_is_non_negative`.
