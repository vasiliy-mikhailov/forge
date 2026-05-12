# `test_when_skill_tier1_prompt_sent_then_reply_completes_within_5_min`

Pins author layer L3.1: the model accepts the full Tier-1 task spec and
finishes within a useful budget.

- **Arrange**: docker-resolved base_url; bench API key from
  `$VLLM_API_KEY` env; `tasks/2048/SKILL_tier1.md` content as user
  message; short static-mode system prompt; `max_tokens=32768`,
  `temperature=0.0`.
- **Act**: `POST {base_url}/v1/chat/completions`, HTTP timeout 300 s.
- **Assert**: response status is `200` AND `choices[0].message.content`
  is a non-empty string.

Test code: [`tests/tier1/test_end_to_end.py`](../../tests/tier1/test_end_to_end.py).
