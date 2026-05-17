# `test_when_execute_submission_called_with_dev_hard_wall_sec_then_score_submission_sees_it`

Pins the per-seed budget threading: when `_execute_submission(...,
dev_hard_wall_sec=N)` is called, `N` flows through to the
DockerCanonicalScorer's `score(..., hard_wall_sec=N)`.

## Contract

- **Arrange**: `captured: dict`. Monkeypatch
  `src.tier1.adapters.docker_canonical_scorer.DockerCanonicalScorer`
  with a `_FakeScorer` whose `.score()` records `hard_wall_sec` into
  `captured` and returns a zero-game `AttemptResult`.
- **Act**: `al._execute_submission(body, workspace, tasks_dir,
  dev_hard_wall_sec=42.0)` with a minimal valid solver body.
- **Assert**: `captured['hard_wall_sec'] == 42.0`.

## Model client injection point

- **Seam**: `DockerCanonicalScorer` class (monkeypatched).
- **Mode**: fake.

Test code: [`../../tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py)::`test_when_execute_submission_called_with_dev_hard_wall_sec_then_score_submission_sees_it`.

## Runtime scope

> **Runtime scope**: unit only.
