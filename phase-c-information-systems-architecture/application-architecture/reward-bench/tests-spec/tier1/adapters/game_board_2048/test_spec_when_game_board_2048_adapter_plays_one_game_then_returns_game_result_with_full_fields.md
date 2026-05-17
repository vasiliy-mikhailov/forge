# `test_when_game_board_2048_adapter_plays_one_game_then_returns_game_result_with_full_fields`
Pins the adapter's return contract: `GameBoard2048Adapter.play_one_game`
returns a fully-populated `GameResult` — every SPEC.md field of the
per-game schema is filled from observable env state. This replaces
the previous `tuple[int, int]` return.
- **Arrange**: import `GameBoard2048Adapter`, `GameResult`. Build a
 trivial inline solver that always returns `'W'` so the game
 terminates deterministically (board fills, state becomes
 `'lost'`).
- **Act**: `adapter.play_one_game(solver, seed=1000)`.
- **Assert**:
 - the return is a `GameResult` instance
 - `result.seed == 1000`
 - `result.score >= 0` (board.score is always non-negative)
 - `result.max_tile >= 2` (every board has at least one tile)
 - `result.moves > 0` (the solver took at least one step)
 - `result.final_state in {'won', 'lost'}` (terminal state)
 - `result.walltime_sec > 0.0` (some wall-clock elapsed)
The richer return shape lets the use case (`score_submission`)
populate `AttemptResult.games` per SPEC.md without the use case
itself measuring moves or walltime — that's an adapter concern.
Test code: [`tests/tier1/adapters/test_game_board_2048.py`](../../../../tests/tier1/adapters/test_game_board_2048.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — GameBoard adapter pure-Python wrapper; scale-invariant.
