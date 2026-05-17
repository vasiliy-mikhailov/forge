# `test_when_composite_given_neither_then_returns_empty`

Pins the empty-input branch of `CompositeParser`: when no child parser
finds anything, the result is `[]` (not exception, not sentinel).

## Contract

- **Arrange**: empty reply `_reply()` (no content, no tool_calls).
  Parser: `CompositeParser([FencedTextParser(), StructuredOpenAIParser()])`.
- **Act**: `parser.extract(reply)`.
- **Assert**: returns `[]`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_composite_given_neither_then_returns_empty`.

## Runtime scope

> **Runtime scope**: unit only.
