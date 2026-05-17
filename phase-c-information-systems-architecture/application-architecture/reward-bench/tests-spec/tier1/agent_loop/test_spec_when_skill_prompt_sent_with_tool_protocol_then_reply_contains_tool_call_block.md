# `test_when_skill_prompt_sent_with_tool_protocol_then_reply_contains_tool_call_block`
Pins agent-loop layer L0 (interactive protocol bootstrap): when the
live model receives the tool-protocol system prompt + a "start the
task" first user message, the reply contains at least one fenced
` ```tool ``` ` block.
This is the foundational behavior of the interactive submission
protocol described in SPEC.md. Without it, no downstream
parse / execute / iterate cycle has real input to test against.
- **Arrange**: `vllm_base_url` fixture; bench API key; `SYSTEM_PROMPT`
 and `FIRST_USER` strings imported from `src.tier1.agent_loop`
 (see `src/tier1/agent_loop.py` SYSTEM_PROMPT); `max_tokens=12288`,
 `temperature=0.0`.
- **Act**: single `POST /v1/chat/completions`, HTTP timeout 600 s.
- **Assert**: response status is `200` AND `choices[0].message.content`
 contains the substring ` ```tool ` (the fence opening for a tool
 call).
Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_skill_prompt_sent_with_tool_protocol_then_reply_contains_tool_call_block`.
