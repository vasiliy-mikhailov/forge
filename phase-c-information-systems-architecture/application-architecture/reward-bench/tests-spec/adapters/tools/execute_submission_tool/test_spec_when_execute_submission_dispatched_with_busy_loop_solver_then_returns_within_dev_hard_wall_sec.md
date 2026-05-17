# `test_spec_when_execute_submission_dispatched_with_busy_loop_solver_then_returns_within_dev_hard_wall_sec`
The cycle-128 adversarial-input test for
[`ExecuteSubmissionTool`](../../../../src-spec/adapters/tools/execute_submission_tool/src_spec_execute_submission_tool_composes_dev_runner.md).
Confirms the dev runner HARD-kills CPU-bound submissions via Docker
isolation (), not soft daemon-thread timeouts.
## The bug this test catches
Pre-cycle-128, `_execute_submission` called `score_submission`
in-process.
Soft timeout works fine for solvers that yield the GIL (`time.sleep`,
I/O, Python-level loops with function calls), but fails completely
for solvers that do pure-Python C-level arithmetic — the daemon
thread keeps running, the main thread is starved, the bench wedges
at 100% CPU forever.
We hit this in production on the post-cycle-123 bench restart:
qwen3.6-27b-fp8 emitted a Monte-Carlo solver; bench wedged at
iter 25/500 of trial 0; killed after 10 min silent.
Per, this is the exact gap a `@live` test with an
adversarial submission catches. Unit tests use scripted Fake
replies that never include busy-loop submissions; cycle-125's
trivial-Solver live test yields the GIL frequently and doesn't
trigger the wedge.
## Contract
- **Arrange**: write an adversarial `Solver` whose `move()` does
 `while time.monotonic() < end: x = x * 1.5` for 60 seconds —
 pure-Python C-level arithmetic, no yield. `dev_hard_wall_sec=30s`.
- **Act**: `tool.dispatch({'content': busy_loop_body}, ctx)`.
 Measure wall time.
- **Assert**:
 - returned within 60s wall time (NOT wedged)
 - observation parses as `<observation>{json}</observation>`
 - `per_seed` is non-empty
 - every per_seed `state` is in `{walltime_exceeded, stagnated, solver_error}`
 — none indicate the solver actually played a game
Test code:
[`tests/adapters/tools/test_execute_submission_tool_busy_loop_live.py`](../../../../tests/adapters/tools/test_execute_submission_tool_busy_loop_live.py).
## Runtime injection points
| runtime | adapter binding | config |
|------------|----------------------------------------------|---------------------------------------|
| unit | `ExecuteSubmissionTool` with autouse fake `_execute_submission` | n/a (unit can't reproduce C-level wedge by definition) |
| **live** | `ExecuteSubmissionTool` + real `_execute_submission` + DockerCanonicalScorer | dev_hard_wall_sec=30, 5 dev seeds, busy-loop solver |
| production | same as live, full agent loop | exercised whenever the model emits a CPU-heavy submission |
## Runtime scope
> **Runtime scope**: live + production — pre-cycle-128 the unit
> runtime couldn't reproduce this bug (Fake's scripted dispatch
> never burns C-level CPU). Live runtime is the only place
> adversarial submissions reach real dev-runner sandboxing.
