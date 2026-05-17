# `test_when_structured_parser_given_one_call_then_extracts`

Pins the basic happy-path of `StructuredOpenAIParser`: one entry in
`reply.tool_calls` with a JSON-string `function.arguments` yields one
`ToolCall` with the parsed args dict.

## Contract

- **Arrange**: `reply = _reply(tool_calls=[{'id': 'x', 'type':
  'function', 'function': {'name': 'view', 'arguments': '{"path":
  "/tasks/2048/SKILL_tier1.md"}'}}])`.
- **Act**: `calls = StructuredOpenAIParser().extract(reply)`.
- **Assert**: `len(calls) == 1`; `calls[0].name == 'view'`;
  `calls[0].args == {'path': '/tasks/2048/SKILL_tier1.md'}`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_structured_parser_given_one_call_then_extracts`.

## Runtime scope

> **Runtime scope**: unit only.
