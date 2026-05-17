# `test_when_solver_init_raises_then_solver_error_final_state`

## Behaviour

When the submission's `Solver.__init__` throws, the worker traps the
exception and reports `final_state == 'solver_error'` with the error
type embedded in `game['error']`.

## Contract

- **Arrange**: write `submission.py` whose `Solver.__init__` raises
  `RuntimeError('synthetic init error')`.
- **Act**: call `_play_one_collect_events((sub, 1, 2048, 100, 60.0, None))`.
- **Assert**: `game['final_state'] == 'solver_error'` and
  `'RuntimeError' in game.get('error', '')`.

## Model client injection point

- **Seam**: `sys.modules['env_2048']` plus the on-disk submission file.
- **Mode**: fake (in-process `_FakeBoard`, no Docker, no LLM).

Test code: [`../../../tests/tier1/tasks/test_runner_canonical.py`](../../../tests/tier1/tasks/test_runner_canonical.py)::`test_when_solver_init_raises_then_solver_error_final_state`.

## Runtime scope

> **Runtime scope**: unit only — runner_canonical worker contract;
> Docker coverage lives in the @live canonical scorer test.
