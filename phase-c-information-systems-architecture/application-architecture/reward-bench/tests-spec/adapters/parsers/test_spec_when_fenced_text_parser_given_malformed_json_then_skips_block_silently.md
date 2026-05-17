# `test_when_fenced_text_parser_given_malformed_json_then_skips_block_silently`

Pins the defensive-parser contract: malformed JSON inside a ```tool
block does NOT raise — the block is skipped, the iter continues with
zero tool calls.

## Contract

- **Arrange**: `reply = _reply(content='```tool\n{this is not json\n```')`.
- **Act**: `FencedTextParser().extract(reply)`.
- **Assert**: returns `[]`. No exception.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_fenced_text_parser_given_malformed_json_then_skips_block_silently`.

## Runtime scope

> **Runtime scope**: unit only.
