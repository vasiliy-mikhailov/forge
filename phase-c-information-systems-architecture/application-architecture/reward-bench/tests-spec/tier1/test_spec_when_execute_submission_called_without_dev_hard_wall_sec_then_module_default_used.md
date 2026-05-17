# `test_when_execute_submission_called_without_dev_hard_wall_sec_then_module_default_used`

Pins back-compat: when `_execute_submission(..., dev_hard_wall_sec=
None)` (or omitted), the module-level default `DEV_HARD_WALL_S` (30s)
is threaded into the scorer instead.

## Contract

- **Arrange**: same `_FakeScorer` pattern recording `hard_wall_sec`.
- **Act**: `al._execute_submission(body, workspace, tasks_dir)` —
  no `dev_hard_wall_sec` kwarg.
- **Assert**: `captured['hard_wall_sec'] == al.DEV_HARD_WALL_S` (30.0).

## Model client injection point

- **Seam**: `DockerCanonicalScorer` class (monkeypatched).
- **Mode**: fake.

Test code: [`../../tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py)::`test_when_execute_submission_called_without_dev_hard_wall_sec_then_module_default_used`.

## Runtime scope

> **Runtime scope**: unit only.
