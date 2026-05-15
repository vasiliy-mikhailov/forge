# `test_when_execute_submission_called_with_syntax_error_body_then_observation_has_syntax_violation`

Pins the **SyntaxError** branch of the `execute_submission`
dispatcher (cycle 58, [ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md)).

When the model emits Python that does not parse, the dispatcher
MUST NOT raise. It MUST return a structured observation JSON with:
  - `protocol_violations` non-empty, containing `'SyntaxError'`
  - `per_seed == []`
  - `mean == 0`

Per [ADR 0002](../../../../docs/adr/0002-main-emits-sentinel-on-malformed-submission.md)
sentinel-on-malformed pattern, the bench converts the parse failure
into a structured signal the model can read.

- **Arrange**: a body with malformed Python (e.g. `</body>\n`).
- **Act**: `execute_tool('execute_submission', {'content': body},
  workspace, env_dir, tasks_dir)`.
- **Assert**: observation `protocol_violations` mentions `SyntaxError`,
  `per_seed == []`, `mean == 0`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
