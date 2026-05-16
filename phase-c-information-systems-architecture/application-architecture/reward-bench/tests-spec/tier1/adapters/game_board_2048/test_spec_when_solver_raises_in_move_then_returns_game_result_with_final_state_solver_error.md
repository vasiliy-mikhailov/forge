# `test_when_solver_raises_in_move_then_returns_game_result_with_final_state_solver_error`

Reproduces the campaign-8 real-system bug: a submission's `Solver.move()`
called `self.machine.to_opening()` where `to_opening` is not a transitions
trigger — `AttributeError` propagated up through `GameBoard2048Adapter.play_one_game`,
through `_play_with_timeout`'s worker, was re-raised in `score_submission`,
escaped to pytest, and failed the campaign with no partial leaderboard data.

Per [ADR 0002](../../../../docs/adr/0002-main-emits-sentinel-on-malformed-submission.md)
the bench should NEVER raise on a malformed submission — it should emit a sentinel
so the leaderboard still gets a data point. ADR 0002 covers static malformations
(missing file, missing class, syntax error). This cycle extends the sentinel
discipline to **runtime** errors inside `solver.move()`.

The adapter is the right layer for the catch because:
- It is the only layer that calls `solver.move()`.
- A solver crash is a property of THIS game (different seeds may succeed),
  not the whole submission. Emitting a per-game sentinel preserves partial
  credit for games that didn't crash.

`'solver_error'` is already a valid `FinalState` in `GameResult` (cycle ~5).

- **Arrange**: build a `_CrashingSolver` whose `move()` raises
  `AttributeError("'to_opening' does not exist")` on the first call.
- **Act**: `GameBoard2048Adapter().play_one_game(_CrashingSolver(), seed=1)`.
- **Assert** (no raise; sentinel returned):
  - Returns a `GameResult` (does NOT raise).
  - `result.final_state == 'solver_error'`.
  - `result.seed == 1`.
  - `result.moves == 0` (crashed before completing any move).
  - `result.walltime_sec >= 0.0`.
  - `result.score >= 0` and `result.max_tile >= 2` (whatever the env started with).

Test code: [`tests/tier1/adapters/test_game_board_2048.py`](../../../../tests/tier1/adapters/test_game_board_2048.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — GameBoard adapter pure-Python wrapper; scale-invariant.

