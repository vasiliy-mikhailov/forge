# `test_when_v1_models_queried_then_qwen3_6_27b_awq_served_name_present`

Pins infrastructure layer L1.2: the correct model is loaded.

- **Arrange**: docker-resolved base_url of the lab vLLM container; bench
  API key from `$VLLM_API_KEY` env.
- **Act**: `GET {base_url}/v1/models`, parse JSON body.
- **Assert**: `qwen3.6-27b-awq` appears in `data[].id`.

Test code: [`tests/tier1/test_inference.py`](../../tests/tier1/test_inference.py).
