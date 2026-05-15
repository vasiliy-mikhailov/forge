# ADR 0010: Mistral special tokens vs the bench's fenced-tool-call protocol

## Status

Accepted (cycle 82, after cycle 78 smoke v2 sweep observed two
mistral-family models smoke-FAIL with zero tool-call extractions).

Partially resolved by cycle 83 (see cycle-95 amendment below): parse_tool_calls now falls back to
OpenAI-structured message.tool_calls when the text-fenced
extraction yields nothing. _call_model returns both content and
tool_calls so the agent loop dispatches Mistral / Devstral /
GPT-OSS without protocol changes for the existing qwen / gemma /
llama path. Spec pin:
[test_spec_when_reply_has_structured_tool_calls_but_no_fenced_blocks_then_parser_extracts_them](../../tests-spec/tier1/agent_loop/test_spec_when_reply_has_structured_tool_calls_but_no_fenced_blocks_then_parser_extracts_them.md).

## Context

The bench's [tool-call protocol](../../src/tier1/agent_loop.py) (cycle
9 / cycle 58) prompts the model to emit tool calls as text inside
fenced code blocks tagged `tool`:

```
```tool
{"name": "execute_submission", "args": {}}
===FILE_BODY===
... raw python ...
```
```

[`parse_tool_calls`](../../src/tier1/agent_loop.py) reads the assistant
reply's `message.content` string and regex-extracts these fenced
blocks. The vLLM serving layer is configured with
`--enable-auto-tool-choice` and a per-model `--tool-call-parser`,
but the bench uses NEITHER the OpenAI tool-call function-calling
schema NOR the resulting structured `message.tool_calls` field — it
reads raw text only.

For most models in the registry (qwen3-*, gemma-4-*, llama-*) this
works because they emit tool calls IN the content field when prompted
with our text-style protocol.

**Mistral family models** (`mistral-small-3.2-24b`,
`devstral-small-2-24b`, `devstral-2-123b*`) are trained to use
Mistral's special-token tool-call format:

| Token | Purpose |
| --- | --- |
| `<s>` | beginning-of-sequence |
| `</s>` | end-of-sequence |
| `[INST]` / `[/INST]` | user-turn wrapper |
| `[AVAILABLE_TOOLS]` / `[/AVAILABLE_TOOLS]` | tool list (JSON) |
| `[TOOL_CALLS]` | model-emitted tool call(s) (JSON array) |
| `[TOOL_RESULTS]` / `[/TOOL_RESULTS]` | tool-result feedback |

When vLLM serves a mistral model with `--tool-call-parser mistral`,
the server extracts `[TOOL_CALLS]` content into the OpenAI-compatible
`response.choices[0].message.tool_calls` STRUCTURED field. The
`message.content` STRING is correspondingly stripped or contains
only non-tool prose. Our `parse_tool_calls` sees the prose and
finds zero ```tool fenced blocks.

Empirical evidence (cycle 78 smoke v2):
  - `mistral-small-3.2-24b`: `no_tool_streak=100` across all
    100 iters. The model IS emitting tool calls, but they live in
    the structured `tool_calls` field which the bench ignores.
  - `devstral-small-2-24b`: model called `finish` at iter 18 but
    every `execute_submission` body the bench DID extract was
    protocol-invalid (no `Solver` class). Likely the mistral
    formatter is splitting the FILE_BODY content across tokens that
    the bench parser doesn't reassemble correctly.

## Decision

This ADR codifies the **known incompatibility** between Mistral's
special-token tool format and the bench's fenced-text tool protocol.
Mistral-family models cannot pass [ADR 0009 v3](
0009-multi-model-smoke-bench-convention.md) smoke until the bench is
extended to consume `response.choices[0].message.tool_calls`
alongside the text-fenced format.

We do NOT change the bench protocol in this ADR — the protocol is a
public contract used by all other registry models. Instead we record
the incompatibility and the path forward.

## Path forward (landed in cycle 83)

Cycle 83 extended
[`parse_tool_calls`](../../src/tier1/agent_loop.py) and
[`_call_model`](../../src/tier1/agent_loop.py) so that:
  1. `_call_model` returns BOTH `message.content` (string) and
     `message.tool_calls` (list, may be empty/absent).
  2. `parse_tool_calls` falls back to the structured field when the
     text-fenced extraction yields nothing.
  3. For `execute_submission`, since the body needs to be raw Python
     (not JSON-escaped) and mistral's structured `function.arguments`
     is JSON, the bench needs a per-tool unmarshaller. The simplest
     route: have mistral's `execute_submission` arguments include a
     JSON-escaped `body` field and the dispatcher un-escapes it.

This is a separate CATS cycle (not cycle 82). Spec the test_spec
first as "when reply has structured tool_calls but no fenced blocks,
`parse_tool_calls` extracts them".

## Consequences

+ Mistral / Devstral smoke FAILs are now documented bugs, not
  "the model can't do 2048".
+ Cycle 78 smoke artefacts for these models accurately record
  "best_dev_mean=None" with a known root cause.
+ The smoke contract (ADR 0009 v3 — "0.0 is a bug") is preserved.
+ Future cycle to make the bench parser polyglot.

## Related

- [ADR 0009](0009-multi-model-smoke-bench-convention.md) — smoke convention.
- [ADR 0008](0008-docker-sandboxed-execute-submission-tool.md) — execute_submission dispatcher.
- [cycle 78 umbrella](../../experiments/leaderboard_data.md) — smoke v2 results.


## Cycle 95 finding — fallback is necessary but not sufficient

Cycle 95 attempted to verify the mistral cohort smoke-PASSes after
cycle 83. It does NOT — for a different reason than cycle 78. With
`--tool-call-parser mistral` enabled, vLLM only extracts `[TOOL_CALLS]`
special-token output into `message.tool_calls` when the request
advertises the available tools via the OpenAI `tools=[...]` array.
The bench never passes `tools`; it relies on `SYSTEM_PROMPT` alone.
Result: mistral correctly answers "I don't have the tools needed"
and emits zero structured tool_calls. Cycle 83's fallback parser is
correct code but has nothing to parse.

Diagnostic from cycle 95 (mistral-small-3.2-24b, 29 iters before
abort):
  - all 29 iters: `tool_calls=0`, `no_tool_streak=29`.
  - direct curl confirmed `message.tool_calls == []` and content =
    "I don't have the tools needed to assist with that."
  - `docker inspect reward-bench-vllm` shows `--tool-call-parser
    mistral` correctly applied.

Path forward (cycle 96, queued):
  1. Define OpenAI tool schemas for `view`, `execute_submission`,
     `finish`.
  2. `_call_model` passes `tools=TOOLS_SCHEMA` per-request.
  3. Regression-test that qwen / gemma / llama still emit text-fenced
     blocks when `tools` is advertised (the schemas shouldn't suppress
     their existing behaviour — content-fenced parser stays the
     default; structured tool_calls remain the fallback).
  4. Rerun cycle 95 smoke v2 against the 6 affected models.
