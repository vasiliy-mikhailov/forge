# `src_spec_when_protocol_parser_extract_called_then_returns_tool_calls`
[`ProtocolParser`](../../../src/ports/protocol_parser.py) — the
runtime-boundary contract for "given an `AssistantReply`, extract the
tool invocations". Established by
[SOLUTION-ARCHITECTURE](../../../SOLUTION-ARCHITECTURE.md).
This port also defines the canonical reply types `AssistantReply` and
`ToolCall` that the rest of the agent loop consumes.
## Types
```python
class AssistantReply(TypedDict):
 content: str # always str (empty allowed)
 tool_calls: list[dict] # OpenAI tool_calls shape; may be empty
class ToolCall(NamedTuple):
 name: str
 args: dict
```
## Contract
```python
class ProtocolParser(Protocol):
 def extract(self, reply: AssistantReply) -> list[ToolCall]:...
```
Semantics:
- `reply` is whatever `ModelClient.call(...)` returned.
- Return is a list of `ToolCall` namedtuples ready for
 `ToolRegistry.dispatch(name, args, ctx)`. Order matches the order
 the model emitted them.
### Liveness / failure semantics
- **MUST NOT raise on malformed input** (the defensive-parser
 contract). Bad JSON in `function.arguments`, unknown schema,
 missing required key — all become "extract found nothing here" and
 return `[]`. The agent loop treats `[]` as "model produced
 text-only this turn".
- **MUST NOT mutate `reply`.** Parsers may be composed
 (`CompositeParser`); each child must see the same input.
## Adapter manifest
- [`FencedTextParser`](../../../src/adapters/parsers/fenced_text_parser.py)
 — ```tool fenced-block extractor over `reply["content"]`. Its
 src_spec covers the fenced-block regex.
- [`StructuredOpenAIParser`](../../../src/adapters/parsers/structured_openai_parser.py)
 — extractor over `reply["tool_calls"]` with SentencePiece-leak
 workaround per
 [SOLUTION-ARCHITECTURE](../../../SOLUTION-ARCHITECTURE.md).
 Its src_spec covers the U+0120 / U+2581 strip.
- [`CompositeParser`](../../../src/adapters/parsers/composite_parser.py)
 — first-non-empty-wins chainer. Its src_spec covers the chaining
 contract (which is its added surface, not the Port contract).
Conftest autouse binds `CompositeParser([FencedTextParser(),
StructuredOpenAIParser()])`.
