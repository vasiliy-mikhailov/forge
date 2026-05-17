# `test_when_run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history`
Pins the loop driver: `run_loop(...)` with `max_iters=1` calls the
model once, executes the tool(s) it returns, and stops. The returned
history is a list of messages including system, first user, the
model's assistant reply, and one user observation block.
- **Arrange**: tmp_path workspace; tasks_dir=REPO/tasks;
 env_dir=REPO/tasks/2048; vllm_base_url + vllm_api_key fixtures;
 `max_iters=1`.
- **Act**: `run_loop(workspace, env_dir, tasks_dir, vllm_base_url,
 vllm_api_key, max_iters=1)`.
- **Assert**: returned dict has `iterations == 1`,
 `len(messages) == 4` (system, first-user, assistant, observation),
 AND `<view path=` appears in the observation (the model is expected
 to start by reading SKILL_tier1.md per the system prompt).
Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
