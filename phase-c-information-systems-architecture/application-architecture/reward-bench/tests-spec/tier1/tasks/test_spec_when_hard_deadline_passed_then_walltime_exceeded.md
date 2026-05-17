# `test_when_hard_deadline_passed_then_walltime_exceeded`

Pins the runner_canonical wall-deadline branch: when `hard_deadline_wall` is already in the past at the start of a game's first iter, the worker emits `final_state='walltime_exceeded'` immediately rather than playing through.

## Contract

- **Arrange**: valid one-move Solver written to tmp_path; `already_past = time.time() - 1.0` (1 s ago).
- **Act**: `_play_one_collect_events((str(sub), 1, 2048, 100, 60.0, already_past))`.
- **Assert**: returned game dict has `final_state == 'walltime_exceeded'`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../../tests/tier1/tasks/test_runner_canonical.py`](../../../tests/tier1/tasks/test_runner_canonical.py)::`test_when_hard_deadline_passed_then_walltime_exceeded`.

## Runtime scope

> **Runtime scope**: unit only.
