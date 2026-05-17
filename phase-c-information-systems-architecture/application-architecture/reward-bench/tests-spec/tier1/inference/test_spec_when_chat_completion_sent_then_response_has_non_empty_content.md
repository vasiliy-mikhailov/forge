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
Test code: [`tests/tier1/test_inference.py`](../../tests/tier1/test_inference.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — inference-orchestration wiring contract; @live coverage at the InferenceOrchestrator level.

Test code: [`../../../tests/tier1/test_inference.py`](../../../tests/tier1/test_inference.py)::`test_when_chat_completion_sent_then_response_has_non_empty_content`.
