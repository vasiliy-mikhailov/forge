# `test_when_composite_given_fenced_block_then_skips_structured`

Pins the `CompositeParser` priority contract: when both surfaces are
present in a reply, the fenced-text result wins and structured
`tool_calls` are ignored. Preserves the documented preference for
the explicit fenced protocol.

## Contract

- **Arrange**: `reply` with content containing a fenced
  `execute_submission` block AND `tool_calls` containing a structured
  `finish` call. Parser:
  `CompositeParser([FencedTextParser(), StructuredOpenAIParser()])`.
- **Act**: `calls = parser.extract(reply)`.
- **Assert**: `len(calls) == 1`; `calls[0].name == 'execute_submission'`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_composite_given_fenced_block_then_skips_structured`.

## Runtime scope

> **Runtime scope**: unit only.
