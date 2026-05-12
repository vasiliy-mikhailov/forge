# Test spec: tier 1 end-to-end (real model → real harness)

Mirrors [`src_spec_end_to_end.md`](../../src-spec/tier1/src_spec_end_to_end.md).
Each entry pins one observable layer. All tests in this file are
implemented in [`tests/tier1/test_end_to_end.py`](../../tests/tier1/test_end_to_end.py)
and run against the live `qwen3.6-27b-bf16` container.

## `test_when_vllm_container_serves_then_v1_models_endpoint_responds`

- **Arrange**: docker-resolved base_url of container
  `vllm-inference` on the `proxy-net` network; bench API
  key from `$VLLM_API_KEY` env.
- **Act**: `GET {base_url}/v1/models` with `Authorization: Bearer
  <api_key>`, HTTP timeout 10 s.
- **Assert**: response status is `200` AND response body is non-empty.

## `test_when_v1_models_queried_then_qwen3_6_27b_bf16_served_name_present`

- **Arrange**: docker-resolved base_url of container
  `vllm-inference` on the `proxy-net` network; bench
  API key from `$VLLM_API_KEY` env.
- **Act**: `GET {base_url}/v1/models`, parse JSON body.
- **Assert**: `qwen3.6-27b-bf16` appears in `data[].id`.

## `test_when_chat_completion_sent_then_response_has_non_empty_content`

- **Arrange**: docker-resolved base_url of `vllm-inference`;
  bench API key from `$VLLM_API_KEY` env; minimal payload with
  `model=qwen3.6-27b-bf16`, single user message `Say hi.`,
  `max_tokens=16`, `temperature=0.0`.
- **Act**: `POST {base_url}/v1/chat/completions` with `Content-Type:
  application/json` and `Authorization: Bearer <api_key>`, HTTP
  timeout 60 s.
- **Assert**: response status is `200` AND `choices[0].message.content`
  is a non-empty string.

## `test_when_skill_tier1_prompt_sent_then_reply_completes_within_5_min`

- **Arrange**: docker-resolved base_url of `vllm-inference`;
  bench API key from `$VLLM_API_KEY` env; `SKILL_tier1.md` read as the
  user message; short static-mode system prompt; `max_tokens=32768`,
  `temperature=0.0`.
- **Act**: `POST {base_url}/v1/chat/completions`, HTTP timeout 300 s.
- **Assert**: response status is `200` AND `choices[0].message.content`
  is a non-empty string.
