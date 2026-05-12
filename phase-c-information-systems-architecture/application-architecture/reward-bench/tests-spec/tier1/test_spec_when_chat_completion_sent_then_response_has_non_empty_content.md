# `test_when_chat_completion_sent_then_response_has_non_empty_content`

Pins protocol layer L2.1: generic chat completion works.

- **Arrange**: docker-resolved base_url; bench API key from
  `$VLLM_API_KEY` env; minimal payload with `model=qwen3.6-27b-awq`,
  single user message `Say hi.`, `max_tokens=16`, `temperature=0.0`.
- **Act**: `POST {base_url}/v1/chat/completions` with
  `Content-Type: application/json` and `Authorization: Bearer
  <api_key>`, HTTP timeout 60 s.
- **Assert**: response status is `200` AND `choices[0].message.content`
  is a non-empty string.

Test code: [`tests/tier1/test_end_to_end.py`](../../tests/tier1/test_end_to_end.py).
