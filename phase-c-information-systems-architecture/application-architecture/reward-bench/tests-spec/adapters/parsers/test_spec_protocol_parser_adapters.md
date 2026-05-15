# `test_spec_protocol_parser_adapters`

Pins the **ProtocolParser port** introduced in cycle 98 per
[ADR 0011](../../../../docs/adr/0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md).

## Why

Pre-cycle-98, `parse_tool_calls` was a single function that knew about
two protocol surfaces (cycle 9/58 text-fenced + cycle 83/96 OpenAI
structured) plus tokenizer leaks (cycle 96). Adding a third surface
would require editing the same function.

Cycle 98 extracts the port [`ProtocolParser`](../../../../src/ports/protocol_parser.py)
with three adapters in [`src/adapters/parsers/`](../../../../src/adapters/parsers/):
  - `FencedTextParser` — text-fenced surface
  - `StructuredOpenAIParser` — OpenAI tool_calls + Ġ-stripping
  - `CompositeParser` — tries children in order; first non-empty wins

`parse_tool_calls` in `agent_loop.py` is now a thin compatibility
shim that delegates to `CompositeParser([FencedTextParser(),
StructuredOpenAIParser()])`. Behaviour unchanged.

## Contract pins

### `FencedTextParser`
- One fenced block → one `ToolCall`.
- `===FILE_BODY===` separator → body merged into `args['content']`.
- Malformed JSON → block skipped silently (cycle 51 defence).
- No blocks → empty list.

### `StructuredOpenAIParser`
- Each `function` entry → one `ToolCall`.
- `function.arguments` as JSON string → parsed. Cycle 96: `Ġ` (U+0120)
  and `▁` (U+2581) stripped before `json.loads`.
- Malformed structured arguments → `(name, {})` (cycle 83 defence).
- `function.arguments` as dict (non-strict vLLM) → used directly.

### `CompositeParser`
- Fenced wins when both surfaces present (cycle 9/58 contract is the
  default; cycle 96 explicitly: "fenced takes priority").
- Falls back to structured ONLY when the first parser yields zero.

## Tests
[`tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../../tests/adapters/parsers/test_protocol_parser_adapters.py).

## Migration constraint
`parse_tool_calls`'s callable signature unchanged. All cycle 91/96
regression tests in `tests/tier1/test_agent_loop.py` continue to pass
without contract changes.
