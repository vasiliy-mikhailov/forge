# `test_spec_when_solver_prints_during_play_then_stdout_suppressed`
Pins the **stdout suppression** added to
[`_play_with_timeout`](../../../../src/tier1/use_cases/score_submission.py).
## Why
's overnight canonical bench produced 156 000 log lines, of
which ~99% were `move called` — a generated Solver's debug `print()`
inside its `move()` method. The bench captured these because the
worker thread that calls `env.play_one_game(solver, seed)` shares the
process's `sys.stdout` with the orchestrator.
The bench's OWN progress prints (`[run_loop] iter X/Y...`,
`[harness] new best dev MEAN=...`) happen OUTSIDE
`env.play_one_game` and MUST remain visible.
## Contract
When `_play_with_timeout` invokes `env.play_one_game(solver, seed)`,
all `sys.stdout` and `sys.stderr` writes performed during that call
go to the system null device. Once `play_one_game` returns (or the
join timeout fires), normal `sys.stdout` / `sys.stderr` are restored.
Bench prints happening BEFORE or AFTER `_play_with_timeout` (e.g.
between seeds in `score_submission`'s loop) are unaffected.
## Model client injection point
- **Seam**: `_play_with_timeout` in `score_submission.py`. The test
 injects a synthetic `env` whose `play_one_game` calls
 `print("solver-stdout-marker")`; the test reads from a stdout
 capture and asserts the marker is absent.
- **Default**: `fake` — no real Solver needed; the synthetic env IS
 the test fixture.
- **Live override**: not applicable — this is a pure unit test.
## Tests
### `test_when_play_one_game_prints_then_stdout_not_captured`
- **Arrange**: a stub `env` whose `play_one_game(solver, seed)` calls
 `print('solver-stdout-marker')` and returns a `GameResult`.
- **Act**: `_play_with_timeout(env, solver, seed=0, timeout=5)` while
 capturing `sys.stdout` via pytest's `capsys` fixture.
- **Assert**: `'solver-stdout-marker'` does NOT appear in captured
 stdout. The returned `GameResult` is whatever the stub returned.
### `test_when_play_one_game_prints_to_stderr_then_stderr_not_captured`
Same as above with `print('marker', file=sys.stderr)`. Assert
`'marker'` is absent from captured stderr.
### `test_when_play_one_game_completes_then_stdout_restored`
- **Arrange**: stub env whose `play_one_game` returns normally.
- **Act**: call `_play_with_timeout`, then `print('after-play')`.
- **Assert**: `'after-play'` IS captured (stdout restored after the
 call).
### `test_when_play_one_game_raises_then_stdout_restored`
Defensive: even on exception, stdout must be restored.
Test code: [`tests/tier1/use_cases/test_score_submission.py`](../../../../tests/tier1/use_cases/test_score_submission.py).
## Runtime scope
> **Runtime scope**: unit only — use-case orchestration over Port mocks; scale-invariant by construction.
