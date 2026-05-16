# `src_spec_tier1_tool_registry_advertises_view_execute_submission_finish`

[`Tier1ToolRegistry`](../../../src/adapters/tier1_tool_registry.py) is the
production [`ToolRegistry`](../../../src/ports/tool_registry.py) binding
for tier 1. Owns the production tier-1 tool surface.

## Contract

`schemas` returns 3 OpenAI tool-call definitions:

| name | params | semantics |
|---|---|---|
| `view` | `path` | read a file from /workspace, /env, or /tasks into the next prompt |
| `execute_submission` | `content` | dev-time sandbox: write the body, run on dev seeds, return JSON observation |
| `finish` | `note` | end the loop; last successful execute_submission body is promoted |

`dispatch(name, args, ctx)`:
- `view`: resolves `args['path']` via `_virt_to_host` (defends ../ escapes
  via post-resolve check); returns `<view path="...">...</view>` or
  `<error>view: ...</error>` on missing file / illegal path.
- `finish`: returns `<finish>{note}</finish>`.
- `execute_submission`: lazy-imports `_execute_submission` and delegates
  (`dev_hard_wall_sec` threaded through ctx per [ADR 0006](../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)).
- Unknown name: returns `<error>unknown tool: {name}</error>`.

Tier 2..4 registries will provide different tool surfaces (langgraph,
openhands, orchestrator) per SPEC.md §Submission Protocols.
