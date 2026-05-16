# ADR 0010 — Mistral / devstral / gpt-oss tool calls go through `tools=[...]` advertisement + structured `message.tool_calls`

## Context

The bench's tool-call protocol (cycle 9 / cycle 58) prompts the model
to emit tool calls as text inside fenced code blocks tagged `tool`:

```
```tool
{"name": "execute_submission", "args": {}}
===FILE_BODY===
... raw python ...
```
```

[`parse_tool_calls`](../../src/tier1/agent_loop.py) reads the assistant
reply's `message.content` string and regex-extracts these blocks. For
the qwen3-*, gemma-4-*, and llama-* families this works because they
emit fenced text in `content` when prompted with the text-style
protocol.

Mistral family models (`mistral-small-3.2-24b`, `devstral-small-2-24b`,
`devstral-2-123b*`, `gpt-oss-*`) are trained to use Mistral-style
special-token tool formats: `[TOOL_CALLS]` produces a JSON array that
vLLM's `--tool-call-parser mistral` extracts into the OpenAI-compatible
`message.tool_calls` STRUCTURED field. `message.content` is stripped
of the tool call.

Two facts about how vLLM uses this:
- vLLM only routes `[TOOL_CALLS]` into `message.tool_calls` when the
  request advertises the available tools via the OpenAI `tools=[...]`
  array. Without the array, mistral answers in prose ("I don't have
  the tools needed") and emits zero structured calls.
- vLLM's mistral tokenizer occasionally leaks SentencePiece space
  tokens (U+0120 `Ġ`, U+2581 `▁`) into the rendered
  `function.arguments` JSON, breaking strict `json.loads`.

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

+ Mistral / devstral / gpt-oss models can drive the bench loop without
  protocol changes for the existing qwen / gemma / llama path.
+ The tokenizer-leak workaround is a one-line defence inside the
  structured parser; doesn't pollute the loop.
+ Adding a third surface (e.g. Anthropic tool-use blocks) is a new
  `ProtocolParser` adapter added to the composite list (per
  [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)),
  not a rewrite of `parse_tool_calls`.
- The bench is now coupled to the OpenAI `tools` schema in addition
  to its prompt-based text-fenced protocol. If a future model server
  uses neither, we add a new model-client adapter.

## Related

- [ADR 0008](0008-docker-sandboxed-execute-submission-tool.md) —
  `execute_submission` tool. The schema lives in `Tier1ToolRegistry`.
- [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  — ports + adapters that make this two-surface parser pluggable.
- Test pin:
  [`test_spec_when_reply_has_structured_tool_calls_but_no_fenced_blocks_then_parser_extracts_them`](../../tests-spec/tier1/agent_loop/test_spec_when_reply_has_structured_tool_calls_but_no_fenced_blocks_then_parser_extracts_them.md).
