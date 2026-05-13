# `test_when_vllm_container_serves_then_v1_models_endpoint_responds`

Pins infrastructure layer L1.1: the live vLLM container responds at all.

- **Arrange**: docker-resolved base_url of the lab vLLM container; bench
  API key from `$VLLM_API_KEY` env.
- **Act**: `GET {base_url}/v1/models` with `Authorization: Bearer
  <api_key>`, HTTP timeout 10 s.
- **Assert**: response status is `200` AND response body is non-empty.

Test code: [`tests/tier1/test_inference.py`](../../tests/tier1/test_inference.py).
