# `src_spec_when_view_tool_executed_then_returns_file_contents`

`src.tier1.agent_loop.execute_tool(name, args, workspace, env_dir, tasks_dir)`,
when called with `name == 'view'`, resolves `args['path']` from a
virtual root (`/workspace`, `/env`, `/tasks`) to a host path, reads the
file, and returns a string of the form:

    <view path="<virt>">
    <file contents>
    </view>

Failure modes:
- Path outside the three allowed virtual roots → `<error>...</error>`.
- File not found → `<error>view: file not found: ...</error>`.

Path translation logic is in `src/tier1/agent_loop.py::_virt_to_host`,
which resolves the virtual prefix to the corresponding host directory
and applies a post-resolve `../` escape check.

Body trim threshold: 4000 chars (`src/tier1/agent_loop.py::_trim`).
