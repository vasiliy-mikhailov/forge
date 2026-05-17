# `test_when_view_dispatched_with_dotdot_escape_then_blocked`

Pins the path-escape defence: a `../` traversal that resolves outside
the allowed root (e.g. `/tasks/../../../etc/passwd`) is blocked with
`<error>` regardless of the literal prefix.

## Contract

- **Arrange**: `tmp_path/ws` and `tmp_path/tasks` dirs.
- **Act**: `Tier1ToolRegistry().dispatch('view',
  {'path': '/tasks/../../../etc/passwd'},
  _ctx(workspace, tmp_path, tmp_path / 'tasks'))`.
- **Assert**: returned string contains `'<error>'`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_view_dispatched_with_dotdot_escape_then_blocked`.

## Runtime scope

> **Runtime scope**: unit only.
