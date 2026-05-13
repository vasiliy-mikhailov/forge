# `src_spec_when_write_file_tool_executed_then_writes_to_workspace`

`execute_tool('write_file', args, workspace, env_dir, tasks_dir)` writes
`args['content']` to the host file path resolved from
`args['path']` via `_virt_to_host`. Returns
`<ok>wrote N chars to <virt></ok>` on success.

Writes are restricted to paths under `/workspace`:
- Paths outside `/workspace` (under `/env` or `/tasks`) → error.
- Paths failing virtual-root resolution → error.

Parent directories are created if missing.

Body for write_file may come from either:
- `args["content"]` set directly by the caller (e.g., a test).
- Tool fence body region after `===FILE_BODY===` line, populated by
  `parse_tool_calls`. The body-region path lands in a later cycle.

This cycle pins only the direct-content path.
