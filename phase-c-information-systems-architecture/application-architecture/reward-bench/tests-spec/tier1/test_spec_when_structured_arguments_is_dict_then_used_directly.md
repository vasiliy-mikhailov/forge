# `test_when_structured_arguments_is_dict_then_used_directly`

Pins the non-strict vLLM branch in the shim: when
`function.arguments` arrives as a Python dict (not a JSON string),
the parser uses it as the args directly.

## Contract

- **Arrange**: `structured = [{'type': 'function', 'function':
  {'name': 'finish', 'arguments': {'note': 'done'}}}]`.
- **Act**: `calls = parse_tool_calls('', structured_tool_calls=structured)`.
- **Assert**: `calls == [('finish', {'note': 'done'})]`.

## Model client injection point

- **Seam**: none — pure function.

Test code: [`../../tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py)::`test_when_structured_arguments_is_dict_then_used_directly`.

## Runtime scope

> **Runtime scope**: unit only.
