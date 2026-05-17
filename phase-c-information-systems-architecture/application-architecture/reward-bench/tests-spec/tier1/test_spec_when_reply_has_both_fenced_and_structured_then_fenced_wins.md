# `test_when_reply_has_both_fenced_and_structured_then_fenced_wins`

Pins the composite-parser priority via the `parse_tool_calls` shim:
when a reply contains BOTH a fenced ```tool block AND structured
`tool_calls`, the fenced surface wins — structured is ignored for
that turn.

## Contract

- **Arrange**: a `reply` string with one fenced `execute_submission`
  block containing `===FILE_BODY===\n# fenced body`. A `structured`
  list with one `finish` tool_call.
- **Act**: `calls = parse_tool_calls(reply, structured_tool_calls=structured)`.
- **Assert**: `len(calls) == 1`; `calls[0]` is
  `('execute_submission', args)` where `args['content'].startswith(
  '# fenced body')`.

## Model client injection point

- **Seam**: none — pure function.

Test code: [`../../tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py)::`test_when_reply_has_both_fenced_and_structured_then_fenced_wins`.

## Runtime scope

> **Runtime scope**: unit only.
