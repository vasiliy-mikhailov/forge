# `test_when_score_submission_called_then_attempt_result_carries_per_game_records_and_derived_flags`
Pins the use case's responsibility to populate the SPEC.md-aligned
fields of `AttemptResult` from the per-game records returned by the
adapter:
- `games` is the tuple of `GameResult` records, one per seed.
- `stagnated_any` is `True` iff any game's `final_state == 'stagnated'`.
- `walltime_exceeded` is `True` iff any game's
 `final_state == 'walltime_exceeded'`.
The test injects a stub `GameEnvPort` that returns hand-crafted
`GameResult` instances with controlled `final_state` values so the
boolean derivation is testable without a live env.
- **Arrange**: import `AttemptResult`, `GameResult`,
 `score_submission`. Build a stub env whose `play_one_game(solver,
 seed)` returns `GameResult` with `final_state='stagnated'` for
 seed 1, `final_state='lost'` for seed 2.
- **Act**: `score_submission(solver_factory=lambda: object(),
 seeds=[1, 2], env=stub)`.
- **Assert**:
 - `len(result.games) == 2`
 - `result.games[0].seed == 1 and result.games[1].seed == 2`
 - `result.stagnated_any is True`
 - `result.walltime_exceeded is False`
Test code: [`tests/tier1/use_cases/test_score_submission.py`](../../../../tests/tier1/use_cases/test_score_submission.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — use-case orchestration; the live coverage for the full scoring path is via @live test_docker_canonical_scorer_live at the Docker boundary.
