# `test_when_write_file_tool_executed_then_writes_to_workspace`

Pins executor layer: the `write_file` tool, given a path under
`/workspace` and a content string, writes the file to disk under the
host workspace directory.

- **Arrange**: temp workspace; `write_file` call with
  `args={"path": "/workspace/submission.py", "content": "<small Python text>"}`.
- **Act**: `execute_tool('write_file', args, workspace, env_dir, tasks_dir)`.
- **Assert**: the host file `workspace / "submission.py"` exists and its
  text equals the supplied content; observation contains `<ok>` and
  the path.

Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
