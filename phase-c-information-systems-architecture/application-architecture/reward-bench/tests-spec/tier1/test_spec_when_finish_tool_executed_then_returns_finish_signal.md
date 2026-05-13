# `test_when_finish_tool_executed_then_returns_finish_signal`

Pins executor layer: the `finish` tool returns an observation with a
`<finish>` tag that the loop driver uses to terminate.

- **Arrange**: temp workspace; `finish` call with
  `args={"note": "all done"}`.
- **Act**: `execute_tool('finish', args, workspace, env_dir, tasks_dir)`.
- **Assert**: result is a string of the form `<finish>...all done...</finish>`.

Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
