# `test_when_solver_valid_then_game_result_returned`

## Behaviour

A well-formed Solver class drives the worker loop to completion and
`_play_one_collect_events` returns a populated game dict alongside an
event list.

## Contract

- **Arrange**: install a fake `env_2048` module, reimport
  `runner_canonical`, and write a `submission.py` whose `Solver.move`
  always returns `'W'`.
- **Act**: call `_play_one_collect_events((sub, 1, 2048, 100, 60.0, None))`.
- **Assert**: `game['seed'] == 1`, `game['score'] >= 0`,
  `game['moves'] > 0`, `game['final_state']` is one of
  `('won', 'lost', 'max_moves')`, and `events` is a list.

## Model client injection point

- **Seam**: `sys.modules['env_2048']` plus the on-disk submission file.
- **Mode**: fake (in-process `_FakeBoard`, no Docker, no LLM).

Test code: [`tests/tier1/tasks/test_runner_canonical.py`](../../../../tests/tier1/tasks/test_runner_canonical.py)::`test_when_solver_valid_then_game_result_returned`.

## Runtime scope

> **Runtime scope**: unit only — runner_canonical worker contract;
> Docker coverage lives in the @live canonical scorer test.
