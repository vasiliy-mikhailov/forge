# `src_spec_when_model_client_called_then_returns_assistant_reply`

[`ModelClient`](../../../src/ports/model_client.py) is the abstraction
the agent loop uses to send messages to an LLM and receive a reply.
Established by [ADR 0011](../../../docs/adr/0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md).

## Contract

A `ModelClient` is anything implementing the `call` operation:

`call(messages, *, tools=None, temperature=0.0, max_tokens=12288, model_id=None) -> AssistantReply`

- `messages`: sequence of message objects (`{role, content}` shape per
  OpenAI Chat Completions).
- `tools`: optional sequence of OpenAI-style tool schemas. When given,
  the underlying server is advertised the available tools so it can
  emit structured `tool_calls` instead of (or alongside) fenced text
  (cycle 96 / ADR 0010).
- `temperature` / `max_tokens` / `model_id`: per-call overrides;
  `model_id=None` falls back to whatever the adapter was constructed
  with.
- Returns `AssistantReply`: a dict with `content: str` and
  `tool_calls: list[dict]` (cycle 83 contract).

Implementations:
- [`VllmOpenAIClient`](../../../src/adapters/vllm_openai_client.py) — production.
- [`FakeModelClient`](../../../src/adapters/fakes/fake_model_client.py) — scripted, for tests.

The protocol carries NO knowledge of the underlying wire format. A future
Anthropic / OpenAI-direct / llama.cpp adapter implements the same shape
without touching the agent loop.
