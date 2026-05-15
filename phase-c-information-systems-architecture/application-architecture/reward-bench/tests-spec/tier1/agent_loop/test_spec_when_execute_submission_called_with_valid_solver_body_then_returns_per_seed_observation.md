# `test_when_execute_submission_called_with_valid_solver_body_then_returns_per_seed_observation`

Pins the **happy-path** for the `execute_submission` dispatcher
introduced in cycle 58 ([ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md)).

When the model emits a valid `Solver` class via the
`===FILE_BODY===` separator inside an `execute_submission` tool
block, the dispatcher MUST return a `<observation>{...}</observation>`
string whose JSON has:
  - `protocol_violations == []`
  - `per_seed` list with entries for `_DEV_SEEDS` (1..5)
  - each `per_seed` entry has `seed`, `score`, `max_tile`, `moves`,
    `state`, `walltime_sec` keys
  - `mean` is a finite non-negative number (not NaN)
  - `max_tile_best >= 2`

Cycle-70 refactor: the dispatcher delegates per-game scoring to
[`score_submission`](../../../../src/tier1/use_cases/score_submission.py),
so the observation schema is preserved by a thin AttemptResult →
JSON transform.

- **Arrange**: temp workspace + tasks dir; a minimal Solver body
  that returns `'W'` for every board.
- **Act**: `execute_tool('execute_submission', {'content': body},
  workspace, env_dir, tasks_dir)`.
- **Assert**: observation JSON shape matches the contract above.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
