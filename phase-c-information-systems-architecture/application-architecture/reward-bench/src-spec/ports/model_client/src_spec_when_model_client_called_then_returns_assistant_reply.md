# `src_spec_when_model_client_called_then_returns_assistant_reply`

[`ModelClient`](../../../src/ports/model_client.py) — the
runtime-boundary contract for "send messages to a model server,
get the assistant reply back". Established by
[ADR 0011](../../../docs/adr/0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md).

Bound by the conftest autouse `_bind_model_client` fixture per
[ADR 0014](../../../docs/adr/0014-test-specs-name-the-dependency-injection-seam.md);
production callers use the `Tier1RunLoopConfig.model_client` field
threaded through DI.

## Contract

```python
class ModelClient(Protocol):
    def call(
        self,
        messages: list[dict],
        *,
        tools: list[dict] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 12288,
        model_id: str | None = None,
    ) -> AssistantReply: ...
```

Where `AssistantReply` is the TypedDict defined in
[`ports/protocol_parser.py`](../../../src/ports/protocol_parser.py)
(`{"content": str, "tool_calls": list[dict]}`).

Semantics:

- `messages` is OpenAI-style chat-completion shape:
  `[{"role": "system"|"user"|"assistant"|"tool", "content": str, ...}]`.
- `tools` advertises the available tool surface per
  [ADR 0010](../../../docs/adr/0010-mistral-devstral-gpt-oss-tool-calls-go-through-tools-advertisement-plus-structured-message-tool-calls.md).
  Mistral-family models route tool calls into `message.tool_calls`;
  text-fenced families ignore the array and keep emitting fenced text
  in `content`. Implementations advertise regardless of family — the
  parser disentangles.
- `temperature`, `max_tokens`, `model_id` mirror OpenAI semantics.
  `model_id=None` means "let the server pick / use the served model
  name".

Return: an `AssistantReply` dict. Normalisation:

- `content` is always a `str` (empty string, never `None`).
- `tool_calls` is always a `list[dict]` (empty list, never `None`,
  never absent).

### Liveness / failure semantics

- **MAY raise on transport failure** (connection refused, 5xx after
  retry, malformed server response). The agent loop treats raise as
  fatal — there's no in-loop recovery path for "vLLM died".
- **MUST NOT raise on a well-formed reply with empty content or
  empty tool_calls** — those are valid model outputs (the parser
  handles them downstream).

## Adapter manifest

- [`VllmOpenAIClient`](../../../src/adapters/vllm_openai_client.py) —
  production adapter (HTTP → `/v1/chat/completions`). Its src_spec
  covers HTTP/auth specifics and the mistral parser arrangement.
- [`FakeModelClient`](../../../src/adapters/fakes/fake_model_client.py)
  — scripted-reply test adapter. Its src_spec covers the `.calls`
  recording surface and `repeat_last` knob.

The protocol carries NO knowledge of the underlying wire format. A
future Anthropic / OpenAI-direct / llama.cpp adapter implements the
same shape without touching the agent loop.
