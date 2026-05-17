# `test_when_solver_move_raises_then_solver_error_with_event`

## Behaviour

When `Solver.move` raises mid-game, the worker records a
`solver_raised` event and finishes with `solver_error`.

## Contract

- **Arrange**: write `submission.py` whose `Solver.move` returns `'W'`
  on the first call and raises `ValueError('synthetic move error')` on
  the second.
- **Act**: call `_play_one_collect_events((sub, 1, 2048, 100, 60.0, None))`.
- **Assert**: `game['final_state'] == 'solver_error'` and at least one
  event in `events` has `event == 'solver_raised'`.

## Model client injection point

- **Seam**: `sys.modules['env_2048']` plus the on-disk submission file.
- **Mode**: fake (in-process `_FakeBoard`, no Docker, no LLM).

Test code: [`tests/tier1/tasks/test_runner_canonical.py`](../../../../tests/tier1/tasks/test_runner_canonical.py)::`test_when_solver_move_raises_then_solver_error_with_event`.

## Runtime scope

> **Runtime scope**: unit only — runner_canonical worker contract;
> Docker coverage lives in the @live canonical scorer test.
