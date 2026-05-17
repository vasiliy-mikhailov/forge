# `test_when_tool_block_parsed_then_yields_name_and_args`
Pins parser layer: given a real model reply containing a fenced
` ```tool ``` ` block with a JSON body, the parser extracts the
`name` and `args` fields as a tuple.
- **Arrange**: session-scoped `tool_protocol_reply` fixture — one
 live chat completion against the lab vLLM using `SYSTEM_PROMPT`
 + `FIRST_USER` from `src.tier1.agent_loop`.
- **Act**: call `src.tier1.agent_loop.parse_tool_calls(reply)`.
- **Assert**: returns a list of at least one `(name, args)` tuple,
 where `name` is a string and `args` is a dict.
Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
