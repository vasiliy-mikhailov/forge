# `test_when_finish_tool_executed_then_returns_finish_signal`
Pins executor layer: the `finish` tool returns an observation with a
`<finish>` tag that the loop driver uses to terminate.
- **Arrange**: temp workspace; `finish` call with
 `args={"note": "all done"}`.
- **Act**: `execute_tool('finish', args, workspace, env_dir, tasks_dir)`.
- **Assert**: result is a string of the form `<finish>...all done...</finish>`.
Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
