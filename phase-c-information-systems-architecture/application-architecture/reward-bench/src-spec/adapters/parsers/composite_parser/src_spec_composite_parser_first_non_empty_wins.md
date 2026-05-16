# `src_spec_composite_parser_first_non_empty_wins`

[`CompositeParser`](../../../src/adapters/parsers/composite_parser.py) —
cycle 98 [`ProtocolParser`](../../../src/ports/protocol_parser.py) that
chains children.

## Contract

`CompositeParser([P1, P2, ...]).extract(reply)`:

For each child parser in order, calls `child.extract(reply)`. Returns
the FIRST non-empty result. If all children return `[]`, returns `[]`.

Production default per cycle 96 (built in `parse_tool_calls` shim and
ADR 0014 conftest binding):

```
CompositeParser([FencedTextParser(), StructuredOpenAIParser()])
```

This preserves the cycle-9/58 text-fenced contract (qwen / gemma /
llama) as the primary surface and falls back to structured only when
the text-fenced pass yields zero.
