# `test_spec_vllm_openai_client_adapter`

Pins the **ModelClient port + VllmOpenAIClient adapter** introduced in
cycle 98b per [ADR 0011](../../../SOLUTION-ARCHITECTURE.md).

## Why

Pre-cycle-98b, `_call_model` in `src/tier1/agent_loop.py` did three
jobs: HTTP transport, OpenAI Chat-Completions payload assembly, and
cycle-96 tool advertisement — all coupled to vLLM. Adding a second
serving stack (Anthropic, OpenAI direct, llama.cpp) would require a
function rewrite.

Cycle 98b extracts the port [`ModelClient`](../../../src/ports/model_client.py)
and the [`VllmOpenAIClient`](../../../src/adapters/vllm_openai_client.py)
adapter. `_call_model` becomes a delegation shim for back-compat with
existing callers (especially tests that monkeypatch the function).

## Contract pins

### `VllmOpenAIClient.call(messages, tools=, temperature=, max_tokens=, model_id=)`
- POSTs to `f'{base_url}/v1/chat/completions'`.
- Sends `Authorization: Bearer {api_key}`.
- Payload contains `model`, `messages`, `max_tokens`, `temperature`.
- Cycle 96: when `tools` is non-empty, payload includes `tools=[...]`.
  When `tools` is None or empty, the `tools` field is OMITTED (so
  servers that reject unknown fields don't choke).
- Per-call `model_id` overrides `default_model_id`.
- Returns `{'content': str, 'tool_calls': list[dict]}` (the cycle-83
  shape).
- Defensive: when the upstream message.content is `None` (mistral
  with structured calls), normalises to `''`.

## Tests
[`tests/adapters/test_vllm_client_adapter.py`](../../../tests/adapters/test_vllm_client_adapter.py)
— 6 contract tests using a stubbed `urllib.request.urlopen` so the
suite stays offline.

## Migration constraint
Pre-cycle-98b callers of `_call_model(base, key, msgs, max_tokens=, temperature=, model_id=)`
must continue to work. The shim takes the same args and constructs
the client + delegates.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — adapter contract; the live coverage for the boundary it crosses lives in the adapter-specific @live test.

