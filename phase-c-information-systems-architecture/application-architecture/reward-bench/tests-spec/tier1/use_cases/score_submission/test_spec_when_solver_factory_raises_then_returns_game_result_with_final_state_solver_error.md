# `test_when_solver_factory_raises_then_returns_game_result_with_final_state_solver_error`

Reproduces the campaign-10 real-system bug: a submission's `Solver.__init__()`
called `self.machine.start()` where `start` is not a transitions trigger.
`AttributeError` propagated up through:
  `score_submission` → `solver_factory()` (raised)
  → pytest

Cycle 28 added a sentinel for crashes inside `solver.move()` (caught in
`GameBoard2048Adapter.play_one_game`). That catch fires too late for
`__init__` crashes — the solver never gets passed to `play_one_game`
because construction itself raises.

Per [ADR 0002](../../../../docs/adr/0002-main-emits-sentinel-on-malformed-submission.md)
the bench should NEVER raise on a malformed submission. ADR 0002 covers
static malformations + cycle 28 extended to `move()` runtime errors. This
cycle extends sentinel discipline to **constructor** runtime errors.

`score_submission` is the right catch layer because:
- It calls `solver_factory()` directly, one level above `play_one_game`.
- A constructor crash is uniform across seeds (every seed will fail the
  same way) BUT we still emit one sentinel per seed so the artifact
  shape contract (`n_games == len(seeds)`) holds.

`'solver_error'` is already a valid `FinalState` in `GameResult`.

- **Arrange**: build a `_CrashingFactory` whose call raises
  `AttributeError("'start' does not exist on <Machine@stub>")`. Stub env
  whose `play_one_game` should never be reached. 3 seeds.
- **Act**: `score_submission(_CrashingFactory, [1,2,3], env, hard_wall_sec=1.0)`.
- **Assert** (no raise; per-seed sentinel returned):
  - Returns an `AttemptResult` (does NOT raise).
  - `result.n_games == 3`.
  - Every `game.final_state == 'solver_error'`.
  - Every `game.score == 0` and `game.moves == 0`.
  - `result.walltime_exceeded is False` (this isn't a walltime bug).

Test code: [`tests/tier1/use_cases/test_score_submission.py`](../../../../tests/tier1/use_cases/test_score_submission.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — use-case orchestration; the live coverage for the full scoring path is via @live test_docker_canonical_scorer_live (cycle 123) at the Docker boundary.

