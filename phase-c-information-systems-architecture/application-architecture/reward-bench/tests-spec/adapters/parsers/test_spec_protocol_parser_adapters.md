# `test_spec_protocol_parser_adapters`
Pins the **ProtocolParser port** introduced per
[SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md).
## Why
Pre-cycle-98, `parse_tool_calls` was a single function that knew about
two protocol surfaces plus tokenizer leaks. Adding a third surface
would require editing the same function.
extracts the port [`ProtocolParser`](../../../../src/ports/protocol_parser.py)
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
- Malformed JSON → block skipped silently.
- No blocks → empty list.
### `StructuredOpenAIParser`
- Each `function` entry → one `ToolCall`.
- `function.arguments` as JSON string → parsed. `Ġ` (U+0120)
 and `▁` (U+2581) stripped before `json.loads`.
- Malformed structured arguments → `(name, {})`.
- `function.arguments` as dict (non-strict vLLM) → used directly.
### `CompositeParser`
- Fenced wins when both surfaces present.
- Falls back to structured ONLY when the first parser yields zero.
## Tests
[`tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../../tests/adapters/parsers/test_protocol_parser_adapters.py).
## Migration constraint
`parse_tool_calls`'s callable signature unchanged. All
regression tests in `tests/tier1/test_agent_loop.py` continue to pass
without contract changes.
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — pure function over `AssistantReply`; no runtime boundary.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_fenced_text_parser_given_one_block_then_extracts_one_call`.
