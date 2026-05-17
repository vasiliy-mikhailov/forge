# `test_when_execute_submission_observation_inspected_then_includes_budget_sec_per_seed`

Pins the first observability fix: the dev_runner observation
returned by `_execute_submission` must include
`budget_sec_per_seed` — the per-seed wall-time budget the dev
runner enforces. Without this field, the model can't size its
solver's per-move work to fit the budget, which contributes to
W-fallback drift (model writes too-deep expectimax, hits walltime
on every seed, scores 0, gives up).

Numerically: `budget_sec_per_seed = dev_hard_wall_sec / len(_DEV_SEEDS)`,
where `_DEV_SEEDS = (1, 2, 3, 4, 5)` so the denominator is 5.

## Contract

- **Arrange**: tmp workspace (`tmp_path/ws`), tmp tasks dir
  (`tmp_path/tasks_dir`). Monkeypatch
  `src.tier1.adapters.docker_canonical_scorer.DockerCanonicalScorer`
  with a stub class that returns a zero-game `AttemptResult` (so the
  function reaches the observation-building path without spawning
  Docker). A minimal valid Solver body using `from transitions
  import` (else protocol_violations short-circuits before reaching
  the field).
- **Act**: `obs_str = _execute_submission(body, workspace, tasks_dir,
  dev_hard_wall_sec=15.0)`. Parse the JSON between
  `<observation>` and `</observation>`.
- **Assert**: `'budget_sec_per_seed' in parsed`;
  `parsed['budget_sec_per_seed'] == pytest.approx(3.0)` (15.0 / 5).

## Model client injection point

- **Seam**: `DockerCanonicalScorer` (monkeypatched to a stub).
- **Mode**: fake — no Docker spawn, no live model.

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_execute_submission_observation_inspected_then_includes_budget_sec_per_seed`.

## Runtime scope

> **Runtime scope**: unit only — observation shape contract.
