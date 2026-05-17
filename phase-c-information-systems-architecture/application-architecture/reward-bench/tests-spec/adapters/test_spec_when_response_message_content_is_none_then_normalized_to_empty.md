# `test_when_response_message_content_is_none_then_normalized_to_empty`
## Behaviour
Mistral with structured tool_calls often returns content=None.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/adapters/test_vllm_client_adapter.py`](../../../../tests/adapters/test_vllm_client_adapter.py)::`test_when_response_message_content_is_none_then_normalized_to_empty`.
## Runtime scope
> **Runtime scope**: unit only — adapter contract; the live coverage for the boundary it crosses lives in the adapter-specific @live test.
