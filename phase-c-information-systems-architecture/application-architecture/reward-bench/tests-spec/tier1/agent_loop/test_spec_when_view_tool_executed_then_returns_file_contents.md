# `test_when_view_tool_executed_then_returns_file_contents`

Pins executor layer: the `view` tool, given an allowed virtual path,
returns the file contents wrapped in a `<view path="...">...</view>`
observation block.

- **Arrange**: a temp workspace; the real `tasks/2048/SKILL_tier1.md`
  as the tasks_dir source; a `view` call with
  `args={"path": "/tasks/2048/SKILL_tier1.md"}`.
- **Act**: `src.tier1.agent_loop.execute_tool('view', args, workspace,
  env_dir, tasks_dir)`.
- **Assert**: result contains `<view path="/tasks/2048/SKILL_tier1.md">`
  and the first few characters of the actual SKILL_tier1.md content.

Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
