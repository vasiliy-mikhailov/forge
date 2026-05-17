# `test_when_solver_returns_invalid_action_then_invalid_action_final_state`

## Behaviour

A non-WASD return value from `Solver.move` ends the game with
`final_state == 'invalid_action'` and records an `invalid_action`
event.

## Contract

- **Arrange**: write `submission.py` whose `Solver.move` returns
  `'Q'` (outside the valid WASD set).
- **Act**: call `_play_one_collect_events((sub, 1, 2048, 100, 60.0, None))`.
- **Assert**: `game['final_state'] == 'invalid_action'` and at least
  one event in `events` has `event == 'invalid_action'`.

## Model client injection point

- **Seam**: `sys.modules['env_2048']` plus the on-disk submission file.
- **Mode**: fake (in-process `_FakeBoard`, no Docker, no LLM).

Test code: [`../../../tests/tier1/tasks/test_runner_canonical.py`](../../../tests/tier1/tasks/test_runner_canonical.py)::`test_when_solver_returns_invalid_action_then_invalid_action_final_state`.

## Runtime scope

> **Runtime scope**: unit only — runner_canonical worker contract;
> Docker coverage lives in the @live canonical scorer test.
