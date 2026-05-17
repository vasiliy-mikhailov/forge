# `test_when_view_dispatched_with_missing_file_then_returns_not_found`

Pins the missing-file branch: a path that resolves under an allowed
root but does not exist returns `'not found'` in the observation
instead of raising.

## Contract

- **Arrange**: `tmp_path/ws` exists but has no `nope.txt`.
- **Act**: `Tier1ToolRegistry().dispatch('view',
  {'path': '/workspace/nope.txt'}, _ctx(workspace, tmp_path, tmp_path))`.
- **Assert**: returned string contains `'not found'`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_view_dispatched_with_missing_file_then_returns_not_found`.

## Runtime scope

> **Runtime scope**: unit only.
