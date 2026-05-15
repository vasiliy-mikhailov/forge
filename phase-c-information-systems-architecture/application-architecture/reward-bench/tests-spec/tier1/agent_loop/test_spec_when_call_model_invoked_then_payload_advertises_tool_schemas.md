# `test_when_call_model_invoked_then_payload_advertises_tool_schemas`

Pins the **OpenAI tools advertisement** added by cycle 96 (ADR 0010
cycle-95 amendment).

## Why

vLLM's per-model `--tool-call-parser` (mistral, openai_oss, etc.) only
routes special-token tool output into `message.tool_calls` when the
request payload includes `tools=[...]` advertising the available
schemas. The bench has historically relied on `SYSTEM_PROMPT` alone,
which works for qwen / gemma / llama (they emit fenced text in
`message.content`) but causes mistral / devstral / gpt-oss to answer
"I don't have the tools needed" with empty `tool_calls`.

Cycle 96 fixes this by passing `tools=TOOL_SCHEMAS` in every
`/v1/chat/completions` request.

## Contract

- `_call_model` includes `tools` in the JSON payload it sends to vLLM.
- The advertised schemas mirror SYSTEM_PROMPT: `view`,
  `execute_submission`, `finish`. Names and required-argument lists
  match exactly so a model that picks either surface produces
  bench-readable tool calls.
- For models that ignore `tools` and keep emitting fenced text
  (qwen / gemma / llama), `tools` is a no-op — `parse_tool_calls`
  reads `message.content` first and only consults
  `message.tool_calls` as a fallback.

## Tests

### Payload includes tools

- **Arrange**: monkeypatch `urllib.request.urlopen` to capture the
  POST body without actually hitting vLLM.
- **Act**: invoke `_call_model('http://stub', 'k', [{'role':'user','content':'x'}])`.
- **Assert**:
  - Captured JSON body has a `'tools'` key.
  - Each entry has `type=='function'` and a non-empty `function.name`.
  - Names exactly = `{'view', 'execute_submission', 'finish'}`.

### Structured-args Ġ-stripping (cycle 96)

vLLM mistral tokenizer leaks U+0120 (`Ġ`, SentencePiece space) and
U+2581 (`▁`, alternate SentencePiece space) into the structured
arguments JSON, e.g.: `{"path":Ġ"SKILL_tier1.md"}`. Plain
`json.loads` rejects this. parse_tool_calls strips the leaked
characters defensively.

- **Arrange**: `structured_tool_calls = [{
    'type': 'function',
    'function': {'name': 'view',
                 'arguments': '{"path":\\u0120"SKILL_tier1.md"}'}}]`
- **Assert**: parser returns `[('view', {'path': 'SKILL_tier1.md'})]`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
