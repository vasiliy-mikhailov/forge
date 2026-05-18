# `test_when_execute_submission_called_then_scorer_score_body_invoked_with_body_string`

Pins the §7.5 migration of `agent_loop._execute_submission` per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7.5. The dev-runner call now goes through `score_body(body=...)`
instead of `score(submission_path=...)`. The body string the model
emits flows directly to the scorer — no path crossing the scorer
boundary.

(Workspace + sub_path file write inside `_execute_submission`
remain for protocol_validate + module-spec load; those go in later
§7.5 cycles.)

- **Arrange**: tmp workspace; minimal valid Solver body; monkeypatch
  `src.tier1.adapters.docker_canonical_scorer.DockerCanonicalScorer`
  with a recording stub that captures the `score_body` call kwargs
  and returns an empty `AttemptResult`.
- **Act**: `agent_loop._execute_submission(body, workspace, tasks_dir,
  dev_hard_wall_sec=15.0)`.
- **Assert**: the stub's `.score_body` was called with `body=BODY`.

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_execute_submission_called_then_scorer_score_body_invoked_with_body_string`.

## Model client injection point

- **Seam**: monkeypatch on
  `src.tier1.adapters.docker_canonical_scorer.DockerCanonicalScorer`.
- **Mode**: **fake** — recording stub.

## Runtime scope

> **Runtime scope**: unit only — kwarg-pass-through test; no Docker spawn.
