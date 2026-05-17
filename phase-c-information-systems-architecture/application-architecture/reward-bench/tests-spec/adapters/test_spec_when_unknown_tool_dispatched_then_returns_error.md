# `test_when_unknown_tool_dispatched_then_returns_error`

Pins the unknown-tool branch: a `name` that isn't in the registry
catalogue (e.g. `'bash'`) returns `'<error>unknown tool: {name}</error>'`
rather than raising. The agent loop sees the error string and can
recover on the next turn.

## Contract

- **Arrange**: any tmp_path (unused by dispatch — unknown name is
  rejected before any filesystem access).
- **Act**: `Tier1ToolRegistry().dispatch('bash', {'cmd': 'rm -rf /'},
  _ctx(tmp_path, tmp_path, tmp_path))`.
- **Assert**: returned string equals `'<error>unknown tool: bash</error>'`.

## Model client injection point

- **Seam**: none — pure name-lookup.

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_unknown_tool_dispatched_then_returns_error`.

## Runtime scope

> **Runtime scope**: unit only.
