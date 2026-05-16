# `test_when_call_model_invoked_then_payload_model_field_matches_served_name`

Pins the **model-name in the chat-completion payload** for
[`_call_model`](../../../../src/tier1/agent_loop.py). The payload
`{"model": ...}` field MUST match the served name vLLM is currently
advertising — otherwise vLLM returns `HTTP 404` for the request.

**Real-world repro (cycle 72 smoke after cycle 73 fix).** Cycle 73
correctly wired `main()` to swap the vLLM container per model via
`ensure_serving_model(target)`. Container becomes e.g. `Qwen3.6-27B-FP8`.
But `_call_model` hardcoded `'model': 'qwen3.6-27b-awq'` in the
request body, so vLLM rejected the request with 404. Every smoke for
a non-AWQ model FAILed with this 404 even though everything else
worked.

Cycle 74 parameterises `_call_model` and the chain feeding it:
  - `_call_model(..., model_id: str)` — uses model_id in payload.
  - `run_loop(..., model_id: str)` — threads through.
  - `main()` passes `target.served_name`.

- **Arrange**: monkeypatch `urllib.request.urlopen` to capture the
  request payload then raise a marker exception so no HTTP call
  actually leaves the process.
- **Act**: `_call_model(vllm_base_url='http://stub', vllm_api_key='k',
  messages=[...], model_id='qwen3.6-27b-fp8')`.
- **Assert**:
  - The captured JSON payload has `model == 'qwen3.6-27b-fp8'`.
  - For backward compatibility, `_call_model` keyword `model_id`
    defaults to `'qwen3.6-27b-awq'` (the historical hardcoded
    value) so older callers don't break.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

