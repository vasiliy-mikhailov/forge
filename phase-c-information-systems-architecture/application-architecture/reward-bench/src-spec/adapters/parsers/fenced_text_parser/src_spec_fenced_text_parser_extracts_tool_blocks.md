# `src_spec_fenced_text_parser_extracts_tool_blocks`

[`FencedTextParser`](../../../src/adapters/parsers/fenced_text_parser.py) —
the cycle-9/58 text-fenced [`ProtocolParser`](../../../src/ports/protocol_parser.py).

## Contract

Reads `reply.content` and finds ` ```tool ... ``` ` fenced blocks. Inside
each block:

1. First non-empty line: a JSON object `{name, args}`.
2. Optional `===FILE_BODY===` separator followed by raw body text,
   merged into `args['content']`.
3. Cycle 51 fallback: malformed JSON → strip trailing commas/whitespace
   and retry once; if still malformed, skip the block silently
   (defensive — bad block must not abort the iter).

Returns `[ToolCall(name, args), ...]` in order of appearance.
