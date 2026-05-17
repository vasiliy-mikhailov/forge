# `test_spec_when_execute_submission_dispatched_with_trivial_solver_then_returns_real_observation`
The cycle-122 live-runtime test for
[`ExecuteSubmissionTool`](../../../../src-spec/adapters/tools/execute_submission_tool/src_spec_execute_submission_tool_composes_dev_runner.md).
Actually invokes the dev sandbox per
[SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
and verifies the returned JSON observation has the expected shape
(non-empty `per_seed`, zero `protocol_violations` for a trivial
Solver, positive `walltime_sec_total`).
Pins the live-test runtime per
[AGENTS](../../../../../AGENTS.md#three-runtimes-two-scales-of-src_spec--unit--live--production).
Unit-runtime variants live in
[`test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py)
(4 monkeypatched execute_submission tests). Production-runtime
coverage is the canonical bench (via run_loop -> ExecuteSubmissionTool).
`view` and `finish` Tools opt out of live-runtime under the
cycle-122 scale-invariant exception (pure-Python; no Docker /
HTTP / subprocess boundary).
## Contract
- **Arrange**: trivial submission body
 `class Solver: def move(self, board): return 'W'`
 written to `tmp_path/workspace/submission.py`. Real
 `ExecuteSubmissionTool()`. `ctx` provides workspace/env_dir/
 tasks_dir + `dev_hard_wall_sec=60`.
- **Act**: `tool.dispatch({'content': trivial_solver}, ctx)`. Really
 spawns Docker.
- **Assert**:
 - return is `str`, parseable as JSON object
 - keys include `per_seed`, `mean`, `walltime_sec_total`
 - `per_seed` is a non-empty list
 - `protocol_violations` is empty (trivial solver is well-formed)
 - `walltime_sec_total > 0` (catches the cycle-123 instant-fail
 fingerprint where Docker silently sentinelizes)
Test code:
[`tests/adapters/tools/test_execute_submission_tool_live.py`](../../../../tests/adapters/tools/test_execute_submission_tool_live.py).
## Runtime injection points
| runtime | adapter binding | config |
|------------|----------------------------------------------|-------------------|
| unit | `Tier1ToolRegistry` with autouse fake `_execute_submission` | UNIT_CONFIG (mocked) |
| **live** | `ExecuteSubmissionTool()` + real `_execute_submission` | dev_hard_wall_sec=60, trivial Solver, 5 dev seeds |
| production | `ExecuteSubmissionTool()` + real `_execute_submission` | full agent_loop submissions; exercised by canonical bench |
## Runtime scope
> **Runtime scope**: live + production — exercises real Docker dev runner via ExecuteSubmissionTool + DockerCanonicalScorer with trivial solver (5 dev seeds, ~10s). Production-runtime coverage via canonical bench + the cycle-128 busy-loop adversarial-input live test.
