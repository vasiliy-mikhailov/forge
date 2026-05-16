# `src_spec_view_tool_resolves_virt_paths_with_escape_protection`

[`ViewTool`](../../../../src/adapters/tools/view_tool.py) — the
[`Tool`](../../../../src/ports/tool.py) adapter that reads files
from /workspace, /env, or /tasks into the next agent prompt.

The Port contract (dispatch returns an observation string) is in
[the Tool Port src_spec](../../../../src-spec/ports/tool/src_spec_when_tool_dispatched_with_args_then_returns_observation_string.md).
This file documents ViewTool's added surface beyond the Port:
virtual-path mapping, `../` escape defence, content trim, and the
specific error-string shapes ViewTool emits.

## Adapter-own surface

### Virtual-path mapping

`ViewTool.dispatch({'path': virt}, ctx)` resolves `virt` to a host
path via three rules:

| `virt` prefix    | host root             |
|------------------|-----------------------|
| `/workspace/X`   | `ctx['workspace']/X`  |
| `/env/X`         | `ctx['env_dir']/X`    |
| `/tasks/X`       | `ctx['tasks_dir']/X`  |

Any `virt` not matching one of these three prefixes returns:

```
<error>view: path must start with /workspace, /env, or /tasks (got '<virt>')</error>
```

### `../` escape defence (defence-in-depth)

After `Path().resolve()`, ViewTool verifies the resolved host path is
still a prefix of the configured root. If `virt='/tasks/../../../etc/passwd'`
resolves outside `ctx['tasks_dir']`, the dispatch returns the
path-prefix error above — NOT the file contents.

Defence-in-depth: even if `Path()` resolves a tricky path through a
symlink or other mechanism, the post-resolve string-prefix check
stops the leak.

### Trim

File contents over 4000 characters are truncated; the result reads:

```
<view path="/tasks/...">
<first ~3800 chars>
... [truncated, total <N> chars]
</view>
```

### Missing file

If the resolved host path doesn't exist:
`<error>view: file not found: <virt></error>`.

### Read failure

If `host.read_text()` raises (encoding error, permission denied,
etc.): `<error>view: <exception message></error>`.

### Empty / missing `path` arg

Resolves to `<error>view: path must start with ...</error>` — the
empty path doesn't match any prefix.

## Test coverage

The following test_specs cover ViewTool's contract; each tests one
distinct behaviour per the cycle-110 one-test-spec-per-contract rule:

- [`test_when_view_dispatched_with_valid_path_then_returns_file_contents`](../../../../tests/adapters/test_tier1_tool_registry.py)
- [`test_when_view_dispatched_with_invalid_root_then_returns_error`](../../../../tests/adapters/test_tier1_tool_registry.py)
- [`test_when_view_dispatched_with_missing_file_then_returns_not_found`](../../../../tests/adapters/test_tier1_tool_registry.py)
- [`test_when_view_dispatched_with_dotdot_escape_then_blocked`](../../../../tests/adapters/test_tier1_tool_registry.py)
