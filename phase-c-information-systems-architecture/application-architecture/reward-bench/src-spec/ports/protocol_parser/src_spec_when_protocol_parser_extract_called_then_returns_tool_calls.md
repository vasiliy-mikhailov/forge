# `src_spec_when_protocol_parser_extract_called_then_returns_tool_calls`

[`ProtocolParser`](../../../src/ports/protocol_parser.py) decodes
assistant replies into `(name, args)` tool-call tuples. Per
[ADR 0011](../../../docs/adr/0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md).

## Contract

`extract(reply: AssistantReply) -> list[ToolCall]`

- `AssistantReply` is the shape `ModelClient.call` returns:
  `{content: str, tool_calls: list[dict]}`.
- `ToolCall` is `NamedTuple(name: str, args: dict)`.
- MUST NOT raise on malformed input (cycle 51 defensive-parser
  contract). On any unrecoverable parse failure for a single block,
  skip that block and continue; if no parseable calls remain, return `[]`.

Implementations:
- [`FencedTextParser`](../../../src/adapters/parsers/fenced_text_parser.py) — cycle 9/58 text-fenced protocol.
- [`StructuredOpenAIParser`](../../../src/adapters/parsers/structured_openai_parser.py) — cycle 83/96 OpenAI structured tool_calls (with Ġ/▁ SentencePiece strip).
- [`CompositeParser`](../../../src/adapters/parsers/composite_parser.py) — tries children in order; first non-empty wins.
