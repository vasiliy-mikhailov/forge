# `test_when_view_tool_executed_then_returns_file_contents`
Pins executor layer: the `view` tool, given an allowed virtual path,
returns the file contents wrapped in a `<view path="...">...</view>`
observation block.
- **Arrange**: a temp workspace; the real `tasks/2048/SKILL_tier1.md`
 as the tasks_dir source; a `view` call with
 `args={"path": "/tasks/2048/SKILL_tier1.md"}`.
- **Act**: `src.tier1.agent_loop.execute_tool('view', args, workspace,
 env_dir, tasks_dir)`.
- **Assert**: result contains `<view path="/tasks/2048/SKILL_tier1.md">`
 and the first few characters of the actual SKILL_tier1.md content.
Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
