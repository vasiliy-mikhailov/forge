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
