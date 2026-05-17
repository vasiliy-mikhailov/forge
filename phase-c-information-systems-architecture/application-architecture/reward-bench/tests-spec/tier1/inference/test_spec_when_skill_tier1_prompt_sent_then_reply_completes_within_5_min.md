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
Test code: [`tests/tier1/test_inference.py`](../../tests/tier1/test_inference.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — inference-orchestration wiring contract; @live coverage at the InferenceOrchestrator level.

Test code: [`../../../tests/tier1/test_inference.py`](../../../tests/tier1/test_inference.py)::`test_when_skill_tier1_prompt_sent_then_reply_completes_within_5_min`.
