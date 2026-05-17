# `test_when_structured_arguments_malformed_then_args_default_to_empty`

Pins the defensive branch in the legacy shim: when
`structured_tool_calls` carries `function.arguments` that's malformed
JSON, the call surfaces as `(name, {})` — no exception, no crash.

## Contract

- **Arrange**: `structured = [{'type': 'function', 'function':
  {'name': 'execute_submission', 'arguments': '{not json'}}]`.
- **Act**: `calls = parse_tool_calls('', structured_tool_calls=structured)`.
- **Assert**: `calls == [('execute_submission', {})]`.

## Model client injection point

- **Seam**: none — pure function.

Test code: [`../../tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py)::`test_when_structured_arguments_malformed_then_args_default_to_empty`.

## Runtime scope

> **Runtime scope**: unit only.
