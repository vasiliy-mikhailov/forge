# `test_when_bash_tool_executed_with_allowed_cmd_then_returns_stdout`

Pins executor layer: the `bash` tool, given a command from the
allow-list, runs the command and returns its stdout/stderr/exit-code
in a `<bash>` observation block.

- **Arrange**: temp workspace; `bash` call with `args={"cmd": "ls /workspace"}`
  (an allow-listed read-only command).
- **Act**: `execute_tool('bash', args, workspace, env_dir, tasks_dir)`.
- **Assert**: result contains `<bash exit=0>` AND the `--- stdout ---`
  section.

Disallowed commands (anything not on the prefix allow-list) return
`<error>bash: command not on allow-list...</error>` — verified by a
second test asserting the error path. That second test is added in
its own cycle when needed.

Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
