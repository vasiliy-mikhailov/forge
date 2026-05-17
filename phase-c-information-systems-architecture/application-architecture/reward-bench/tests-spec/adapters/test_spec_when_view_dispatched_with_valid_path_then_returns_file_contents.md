# `test_when_view_dispatched_with_valid_path_then_returns_file_contents`

Pins the `view` tool happy-path: given a real file inside one of the
allowed virtual roots (`/workspace`, `/env`, `/tasks`), the dispatcher
returns the file contents wrapped in `<view path="...">...</view>`.

## Contract

- **Arrange**: `tmp_path/ws`, `tmp_path/env`, `tmp_path/tasks` dirs;
  `tasks_dir/hello.txt` written with `'hello world'`.
- **Act**: `Tier1ToolRegistry().dispatch('view',
  {'path': '/tasks/hello.txt'}, _ctx(workspace, env_dir, tasks_dir))`.
- **Assert**: returned string contains `'<view path="/tasks/hello.txt">'`
  AND `'hello world'`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake (real file in tmp directory).

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_view_dispatched_with_valid_path_then_returns_file_contents`.

## Runtime scope

> **Runtime scope**: unit only.
