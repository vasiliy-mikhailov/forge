# `src_spec_execute_submission_tool_composes_dev_runner`
[`ExecuteSubmissionTool`](../../../../src/adapters/tools/execute_submission_tool.py)
— the [`Tool`](../../../../src/ports/tool.py) adapter that writes a
submission body to `/workspace`, runs it in the dev sandbox, and
returns the per-seed observation JSON string.
The Port contract is in
[the Tool Port src_spec](../../../../src-spec/ports/tool/src_spec_when_tool_dispatched_with_args_then_returns_observation_string.md).
This file documents ExecuteSubmissionTool's added surface:
composition with `_execute_submission`.
## Adapter-own surface
### Composition
`ExecuteSubmissionTool.dispatch({'content': body}, ctx)`:
1. **Lazy-imports** `_execute_submission` from
 [`src.tier1.agent_loop`](../../../../src/tier1/agent_loop.py).
 Lazy because:
 - avoids the `agent_loop -> tools -> agent_loop` import cycle that
 a module-level import would create;
 - keeps the adapter constructable in tests that don't exercise
 the dev runner.
2. Calls `_execute_submission(body, ctx['workspace'], ctx['tasks_dir'],
 dev_hard_wall_sec=ctx.get('dev_hard_wall_sec'))`.
3. Returns the JSON observation string the dev runner produces.
### Dev-runner contract (per
[SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md))
`_execute_submission`:
- Writes `body` to `<workspace>/submission.py`.
- Runs against dev seeds (default `(1, 2, 3, 4, 5)`).
- Returns a JSON string with keys: `protocol_violations`,
 `per_seed`, `mean`, `median`, `max_tile_best`,
 `walltime_sec_total`, `budget_sec_per_seed` (= dev_hard_wall_sec / 5).
- Honours `dev_hard_wall_sec` (per
 [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
 Layer 1 /) — overshoot becomes per-seed `walltime_exceeded`.
- Sandboxes the body inside the `reward-bench-tier1` Docker image — hostile submissions cannot escape.
### Args contract
| key | required | meaning |
|-----------|----------|--------------------------------------------|
| `content` | yes | Full Python submission body (string). |
`args.get('content', '')` defaults to empty string. The dev runner
sees that as an empty submission and returns a `protocol_violations`
observation describing it — ExecuteSubmissionTool itself never
raises.
## Test coverage
- [`test_when_execute_submission_called_with_valid_solver_body_then_returns_per_seed_observations`](../../../../tests/tier1/test_agent_loop.py)
- [`test_when_execute_submission_called_with_syntax_error_body_then_observation_has_syntax_violation`](../../../../tests/tier1/test_agent_loop.py)
- [`test_when_execute_submission_called_with_gym_style_body_then_observation_has_protocol_violation`](../../../../tests/tier1/test_agent_loop.py)
- [`test_when_execute_submission_called_with_slow_solver_then_per_seed_reports_walltime_exceeded`](../../../../tests/tier1/test_agent_loop.py)
