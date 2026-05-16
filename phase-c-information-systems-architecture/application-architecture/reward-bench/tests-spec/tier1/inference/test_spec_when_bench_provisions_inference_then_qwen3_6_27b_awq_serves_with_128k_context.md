# `test_when_bench_provisions_inference_then_qwen3_6_27b_awq_serves_with_128k_context`

Pins the benchs ability to bring up its own inference. No reliance
on an operator having started the container manually.

- **Arrange**: bench API key from `$VLLM_API_KEY` env; the lab GPU
  (Blackwell) is reachable to Docker; no other process holds the
  `reward-bench-vllm` container name.
- **Act**: call `bench.tier1.inference.ensure_serving()`.
- **Assert**: the helper returns a base_url; `GET {base_url}/v1/models`
  returns 200 and lists `qwen3.6-27b-awq` with `max_model_len` >= 131072.

Test code: [`tests/tier1/test_inference.py`](../../tests/tier1/test_inference.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

