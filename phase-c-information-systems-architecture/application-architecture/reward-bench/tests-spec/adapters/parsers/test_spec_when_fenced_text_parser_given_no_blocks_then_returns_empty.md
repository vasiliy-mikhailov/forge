# `test_when_fenced_text_parser_given_no_blocks_then_returns_empty`

Pins the empty-input branch: when `content` contains no ```tool
fenced blocks at all, the parser returns an empty list (not a
sentinel, not an exception).

## Contract

- **Arrange**: `reply = _reply(content='just prose')`.
- **Act**: `FencedTextParser().extract(reply)`.
- **Assert**: returns `[]`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_fenced_text_parser_given_no_blocks_then_returns_empty`.

## Runtime scope

> **Runtime scope**: unit only.
