# `test_when_reply_has_structured_tool_calls_but_no_fenced_blocks_then_parser_extracts_them`

Pins the **structured-tool-calls fallback** in
[`parse_tool_calls`](../../../../src/tier1/agent_loop.py) per
[ADR 0010 §Path forward](../../../../docs/adr/0010-mistral-special-tokens-incompatible-with-fenced-tool-protocol.md):

> A future cycle will extend `parse_tool_calls` and `_call_model` so that:
>   1. `_call_model` returns BOTH `message.content` and `message.tool_calls`.
>   2. `parse_tool_calls` falls back to the structured field when the
>      text-fenced extraction yields nothing.
>   3. For `execute_submission`, function.arguments is JSON; the body
>      lives in args["content"].

Cycle 83 lands this.

## Why

vLLM with `--tool-call-parser mistral` (and similarly for gpt-oss /
devstral) extracts the model's `[TOOL_CALLS]` special-token output
into the OpenAI-compatible `message.tool_calls` STRUCTURED field. The
text `message.content` is stripped of the tool call. Our cycle-9/58
fenced-text parser therefore sees zero tool calls and the iter
counts as `no_tool_streak`.

This forced 5 registry models (mistral-small-3.2-24b, devstral-*,
gpt-oss-20b, gpt-oss-120b) to smoke-FAIL despite the model
correctly emitting tool calls.

## Contract

`parse_tool_calls(reply: str, structured_tool_calls: list | None = None) -> list[tuple[str, dict]]`

- When `reply` contains text-fenced tool blocks: extract from those
  (cycle 9/58 path, default).
- When fenced extraction yields ZERO calls AND `structured_tool_calls`
  is non-empty: iterate the structured list. For each entry, read
  `function.name` and `function.arguments`. `arguments` is a JSON
  string per OpenAI spec — `json.loads` it; if the parse fails or
  the result is not a dict, fall back to empty args.

We do NOT mix the two surfaces in a single reply. A model talks one
protocol or the other; the structured field is purely a fallback.

## Test cases

### Mistral-style structured call only

- **Arrange**: `reply=""` (empty content; mistral stripped it).
  `structured_tool_calls=[
     {"id": "x", "type": "function",
      "function": {"name": "execute_submission",
                   "arguments": '{"content": "class Solver: ..."}'}}
  ]`
- **Act**: `parse_tool_calls(reply, structured_tool_calls=...)`.
- **Assert**:
  - Exactly one (name, args) tuple returned.
  - `name == 'execute_submission'`.
  - `args['content'].startswith('class Solver:')`.

### Fenced takes priority over structured

When both surfaces are present, the fenced format wins (cycle-9/58
default protocol). Models in the qwen / gemma / llama family don't
ship structured tool_calls in practice; this assertion guards us
against a future server config change that does.

- **Arrange**: `reply` contains one fenced `execute_submission` block;
  structured list also has a (different) `finish` call.
- **Assert**: exactly one tuple, and it's the fenced
  `execute_submission` — the structured `finish` is ignored.

### Defensive: malformed structured arguments

- **Arrange**: structured entry with `arguments="{not json"`.
- **Act**: parse.
- **Assert**: tuple returned with `args == {}` (empty dict), name
  preserved. The dispatcher will see no content and emit its usual
  protocol-violation observation; the iter is not aborted.

### Defensive: arguments as dict (some vLLM versions)

- **Arrange**: structured entry with `arguments={"content": "..."}` as
  a dict (not a string).
- **Assert**: extracted as-is.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

