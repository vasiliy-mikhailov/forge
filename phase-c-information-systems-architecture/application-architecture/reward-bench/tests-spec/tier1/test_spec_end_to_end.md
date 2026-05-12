# Test spec: tier 1 end-to-end (real model → real harness)

Mirrors [`code_spec_end_to_end.md`](../../src-spec/tier1/code_spec_end_to_end.md).
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
