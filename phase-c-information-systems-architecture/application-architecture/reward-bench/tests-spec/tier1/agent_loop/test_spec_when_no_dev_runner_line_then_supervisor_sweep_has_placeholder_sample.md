# `test_when_no_dev_runner_line_then_supervisor_sweep_has_placeholder_sample`
Pins the **placeholder** branch of the supervisor sweep accumulator
introduced per [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md).
The supervisor consults `_sweep_samples` every `supervisor_every_k`
iters. Each iter contributes a sample `(iter_n, mean_score,
max_tile, walltime)`. When the iter's tool observation produces
**no** `dev_runner` summary line (e.g. the tool was `view`, not
`bash` / `execute_submission`), the sample MUST be the
placeholder `(iter_n, 0.0, 0, 0.0)` rather than skipped — this
keeps the sample-per-iter contract that supervisor's plateau
heuristic relies on.
- **Arrange**: stub `_call_model` to emit a single `view` tool
 call (no dev_runner stdout).
- **Act**: `run_loop(..., supervisor=<recorder>, supervisor_every_k=1)`.
- **Assert**: the supervisor receives a sweep sample
 `(iter_n, 0.0, 0, 0.0)` for that iter.
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
