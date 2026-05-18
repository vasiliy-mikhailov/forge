# `test_when_execute_submission_called_then_workspace_submission_py_is_not_written`

§7.5 cleanup: `_execute_submission` no longer writes the body to
`workspace/submission.py` for module loading. The body is compiled
in memory (same pattern as `InProcessCanonicalScorer.score_body`).
Per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7.5: workspace is a private implementation detail of the scorer
adapter, not an interface between the agent loop and code loading.

- **Arrange**: tmp workspace; minimal valid Solver body; monkeypatch
  `DockerCanonicalScorer` with a stub that returns an empty
  `AttemptResult`.
- **Act**: `agent_loop._execute_submission(BODY, workspace,
  tasks_dir, dev_hard_wall_sec=15.0)`.
- **Assert**: `(workspace / 'submission.py').exists() is False` —
  the workspace was NEVER written to during execution.

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_execute_submission_called_then_workspace_submission_py_is_not_written`.

## Model client injection point

- **Seam**: monkeypatch on `DockerCanonicalScorer`.
- **Mode**: **fake** — recording stub.

## Runtime scope

> **Runtime scope**: unit only — no workspace write, no Docker spawn.
