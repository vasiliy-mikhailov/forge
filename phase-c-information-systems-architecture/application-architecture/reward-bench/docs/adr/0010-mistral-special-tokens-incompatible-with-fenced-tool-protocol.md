# ADR 0010 — Mistral / devstral / gpt-oss tool calls go through `tools=[...]` advertisement + structured `message.tool_calls`

## Context

The bench tool-call protocol prompts the model to emit tool calls as
fenced text:

```
```tool
{"name": "execute_submission", "args": {}}
===FILE_BODY===
... raw python ...
```
```

[`parse_tool_calls`](../../src/tier1/agent_loop.py) regex-extracts
these from `message.content`. Works for qwen3-*, gemma-4-*, llama-*.

Mistral-family models (`mistral-small-3.2-24b`, `devstral-small-2-24b`,
`devstral-2-123b*`, `gpt-oss-*`) use Mistral special tokens:
`[TOOL_CALLS]` → vLLM's `--tool-call-parser mistral` → OpenAI structured
`message.tool_calls`. `message.content` is stripped.

Two vLLM facts:
- Routes `[TOOL_CALLS]` only when the request advertises `tools=[...]`.
  Without it, mistral answers in prose ("I don't have the tools needed").
- The mistral tokenizer occasionally leaks SentencePiece space tokens
  (U+0120 `Ġ`, U+2581 `▁`) into `function.arguments`, breaking strict
  `json.loads`.

## Decision

The bench:

1. **Advertises tools on every request.** `_call_model` passes a
   `tools=TOOL_SCHEMAS` list mirroring `SYSTEM_PROMPT` (the
   `Tier1ToolRegistry.schemas` catalog). Text-fenced models ignore it
   and keep emitting fenced text; mistral-family models use it to
   route through `message.tool_calls`.

2. **Reads both surfaces.** `parse_tool_calls` is a composite of
   [`FencedTextParser`](../../src/adapters/parsers/fenced_text_parser.py)
   over `message.content` and
   [`StructuredOpenAIParser`](../../src/adapters/parsers/structured_openai_parser.py)
   over `message.tool_calls`. Fenced wins when both are present
   (cycle 9/58 contract is the default); structured is the fallback.

3. **Strips SentencePiece leaks before `json.loads`.** The structured
   parser replaces U+0120 / U+2581 with a space in
   `function.arguments` before parsing. No-op on well-formed JSON.

`_call_model` returns the OpenAI `AssistantReply` shape
`{'content': str, 'tool_calls': list[dict]}` so the loop can dispatch
either surface uniformly.

## Consequences

+ Mistral / devstral / gpt-oss drive the loop without changing the
  existing qwen/gemma/llama path.
+ Tokenizer leak workaround is one line in the structured parser.
+ A third surface (e.g. Anthropic tool-use blocks) is a new
  `ProtocolParser` adapter (per [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)),
  not a rewrite.
- Bench is now coupled to the OpenAI `tools` schema in addition to the
  fenced protocol. A new server type means a new model-client adapter.

## Related

- [ADR 0008](0008-docker-sandboxed-execute-submission-tool.md) —
  `execute_submission` tool. The schema lives in `Tier1ToolRegistry`.
- [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  — ports + adapters that make this two-surface parser pluggable.
- Test pin:
  [`test_spec_when_reply_has_structured_tool_calls_but_no_fenced_blocks_then_parser_extracts_them`](../../tests-spec/tier1/agent_loop/test_spec_when_reply_has_structured_tool_calls_but_no_fenced_blocks_then_parser_extracts_them.md).
