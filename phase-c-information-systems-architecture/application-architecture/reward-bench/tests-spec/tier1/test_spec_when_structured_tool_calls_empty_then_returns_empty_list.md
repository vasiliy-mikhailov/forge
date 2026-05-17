# `test_when_structured_tool_calls_empty_then_returns_empty_list`

Pins the empty-input branch of `parse_tool_calls`: empty content +
empty/None/missing structured list returns `[]` — no exception.

## Contract

- **Arrange**: none.
- **Act**: `parse_tool_calls('')`; `parse_tool_calls('',
  structured_tool_calls=[])`; `parse_tool_calls('',
  structured_tool_calls=None)`.
- **Assert**: each call returns `[]`.

## Model client injection point

- **Seam**: none — pure function.

Test code: [`../../tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py)::`test_when_structured_tool_calls_empty_then_returns_empty_list`.

## Runtime scope

> **Runtime scope**: unit only.
