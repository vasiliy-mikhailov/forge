# `test_when_write_file_tool_executed_then_writes_to_workspace` (LEGACY)

**Status**: `write_file` is a LEGACY tool per [ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md).
The active tool for shipping a submission is `execute_submission`.
`write_file` is retained behind `--legacy-write-file` for one
transitional cycle so existing tests + the `legacy_agent_loop.py`
blessed runner (per [ADR 0007](../../../../docs/adr/0007-per-model-bench-uses-blessed-runner-until-agent-loop-bisect.md))
keep working until ADR 0007 is superseded.

When ADR 0007 is superseded, this test_spec MAY be retired (along
with the `write_file` tool implementation). Until then it pins the
legacy contract: `write_file` writes to `/workspace/<path>` (only,
not `/env` or `/tasks`).

- **Arrange**: `tmp_path` workspace; tool args
  `{'path': '/workspace/foo.py', 'content': 'print("ok")\n'}`.
- **Act**: `execute_tool('write_file', args, workspace, env_dir, tasks_dir)`.
- **Assert**: `(workspace / 'foo.py').read_text() == 'print("ok")\n'`
  AND the observation indicates success (no `<error>` tag).

Sibling negative test pins refusal to write outside `/workspace`
(security boundary inherited from cycle 11).

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
