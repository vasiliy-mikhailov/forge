# `test_when_execute_submission_called_with_slow_solver_then_per_seed_reports_walltime_exceeded`
Pins the **dev-path wall-time protection** in
[`_execute_submission`](../../../../src/tier1/agent_loop.py).
deletes the duplicate inline game loop and delegates per-game
scoring to
[`score_submission`](../../../../src/tier1/use_cases/score_submission.py)
so the dev feedback path inherits the timeout +
sentinel infrastructure already pinned by tests in
`tests/tier1/use_cases/`.
**Real-world repro.** The model wrote
an `expectimax(depth=4)` Solver with `deepcopy`; each `move()` was
multiple seconds; with the old 3000-move cap and no wall-time check,
the dev path wedged for hours. The canonical scorer would have
sentinel'd it under its per-trial budget. The dev path now does too.
The observation JSON schema is **preserved** (the cycle-63
`_parse_dev_runner_summary` keeps working). What changes: `state`
now ranges over the canonical-scorer set (`won`, `lost`,
`walltime_exceeded`, `solver_error`, `stagnated`) instead of an
ad-hoc set.
- **Arrange**: a protocol-valid `Solver` whose `move()` sleeps
 longer than `DEV_HARD_WALL_S` (the agent_loop module constant,
 monkeypatched small for test speed).
- **Act**: call `execute_tool('execute_submission',...)`.
- **Assert**:
 - The call returns within a bounded wall-time (much less than the
 "wedges for hours" baseline).
 - `payload['protocol_violations'] == []`.
 - At least one `per_seed` entry has `state == 'walltime_exceeded'`.
 - `mean`, `median` are numbers (not NaN).
 - The observation parses cleanly via the cycle-63 parser shape.
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
