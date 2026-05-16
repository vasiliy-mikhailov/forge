# `src_spec_structured_openai_parser_handles_mistral_calls`

[`StructuredOpenAIParser`](../../../src/adapters/parsers/structured_openai_parser.py)
— cycle 83 / 96 [`ProtocolParser`](../../../src/ports/protocol_parser.py)
that reads the OpenAI structured `tool_calls` field.

## Contract

Reads `reply.tool_calls` (a list of OpenAI tool-call objects). For each:

1. Extracts `function.name` (must be non-empty).
2. Parses `function.arguments`:
   - If a string: cycle 96 SentencePiece strip (U+0120 `Ġ` → space,
     U+2581 `▁` → space — vLLM mistral tokenizer leaks these),
     then `json.loads`.
   - If a dict (some non-strict vLLM modes): use directly.
   - On `JSONDecodeError` or any unexpected shape: `args = {}` (cycle 83
     defensive).

Returns `[ToolCall(name, args), ...]` preserving input order.
