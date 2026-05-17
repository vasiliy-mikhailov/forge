# `test_when_fenced_text_parser_given_one_block_then_extracts_one_call`

Pins the basic happy-path of `FencedTextParser`: one ```tool fenced
JSON block in `content` yields one `ToolCall` with the JSON's `name`
and `args` round-tripped.

## Contract

- **Arrange**: `reply = {'content': '```tool\n{"name": "view", "args":
  {"path": "/tasks/2048/SKILL_tier1.md"}}\n```', 'tool_calls': []}`.
- **Act**: `calls = FencedTextParser().extract(reply)`.
- **Assert**: `len(calls) == 1`; `calls[0].name == 'view'`;
  `calls[0].args == {'path': '/tasks/2048/SKILL_tier1.md'}`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_fenced_text_parser_given_one_block_then_extracts_one_call`.

## Runtime scope

> **Runtime scope**: unit only.
