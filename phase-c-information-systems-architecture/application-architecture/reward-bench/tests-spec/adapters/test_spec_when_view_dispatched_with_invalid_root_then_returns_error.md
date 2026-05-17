# `test_when_view_dispatched_with_invalid_root_then_returns_error`

Pins the path-allowlist contract: a path that starts with something
other than `/workspace`, `/env`, or `/tasks` (e.g. `/etc/passwd`) is
rejected with an `<error>view:` string instead of dispatching to the
filesystem.

## Contract

- **Arrange**: `tmp_path` as all three roots (simplest setup).
- **Act**: `Tier1ToolRegistry().dispatch('view',
  {'path': '/etc/passwd'}, _ctx(tmp_path, tmp_path, tmp_path))`.
- **Assert**: returned string contains `'<error>view:'` AND
  `'/etc/passwd'` (echoed back so the agent sees what was rejected).

## Model client injection point

- **Seam**: filesystem (tmp_path roots, not reached).
- **Mode**: fake.

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_view_dispatched_with_invalid_root_then_returns_error`.

## Runtime scope

> **Runtime scope**: unit only.
