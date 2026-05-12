# Test spec: tier 1 end-to-end (real model → real harness)

Mirrors [`src_spec_end_to_end.md`](../../src-spec/tier1/src_spec_end_to_end.md).
Each entry pins one observable layer. All tests in this file are
implemented in [`tests/tier1/test_end_to_end.py`](../../tests/tier1/test_end_to_end.py)
and run against the live `qwen3.6-27b-awq` container.

## `test_when_vllm_container_serves_then_v1_models_endpoint_responds`

- **Arrange**: docker-resolved base_url of container
  `omega-reptile-vllm-playground` on the `proxy-net` network; bench API
  key from `$VLLM_API_KEY` env.
- **Act**: `GET {base_url}/v1/models` with `Authorization: Bearer
  <api_key>`, HTTP timeout 10 s.
- **Assert**: response status is `200` AND response body is non-empty.

## `test_when_v1_models_queried_then_qwen3_6_27b_awq_served_name_present`

- **Arrange**: docker-resolved base_url of container
  `omega-reptile-vllm-playground` on the `proxy-net` network; bench
  API key from `$VLLM_API_KEY` env.
- **Act**: `GET {base_url}/v1/models`, parse JSON body.
- **Assert**: `qwen3.6-27b-awq` appears in `data[].id`.

## `test_when_chat_completion_sent_then_response_has_non_empty_content`

- **Arrange**: docker-resolved base_url of `omega-reptile-vllm-playground`;
  bench API key from `$VLLM_API_KEY` env; minimal payload with
  `model=qwen3.6-27b-awq`, single user message `Say hi.`,
  `max_tokens=16`, `temperature=0.0`.
- **Act**: `POST {base_url}/v1/chat/completions` with `Content-Type:
  application/json` and `Authorization: Bearer <api_key>`, HTTP
  timeout 60 s.
- **Assert**: response status is `200` AND `choices[0].message.content`
  is a non-empty string.
