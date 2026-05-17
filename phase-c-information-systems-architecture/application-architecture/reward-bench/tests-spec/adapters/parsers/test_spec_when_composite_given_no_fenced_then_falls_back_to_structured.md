# `test_when_composite_given_no_fenced_then_falls_back_to_structured`

Pins the fallback branch of `CompositeParser`: when the fenced parser
yields zero calls, the next parser in the list (structured) runs and
its result is returned.

## Contract

- **Arrange**: `reply` with empty content and a single structured
  `view` tool_call. Parser:
  `CompositeParser([FencedTextParser(), StructuredOpenAIParser()])`.
- **Act**: `calls = parser.extract(reply)`.
- **Assert**: `len(calls) == 1`; `calls[0].name == 'view'`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_composite_given_no_fenced_then_falls_back_to_structured`.

## Runtime scope

> **Runtime scope**: unit only.
