# `src_spec_when_tool_registry_consulted_then_provides_schemas_and_dispatch`

[`ToolRegistry`](../../../src/ports/tool_registry.py) catalogs the tools
the model can invoke and dispatches tool calls to handlers. Per
[ADR 0011](../../../docs/adr/0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md).

## Contract

A `ToolRegistry` exposes two seams:

- `schemas: tuple[dict, ...]` — OpenAI tool-call schemas advertised
  on each `ModelClient.call(tools=...)` request (cycle 96).
- `dispatch(name, args, ctx) -> str` — given a tool call (name + args
  dict) and a per-iter `ToolContext` (workspace/env_dir/tasks_dir +
  optional dev_hard_wall_sec), returns the observation string for the
  next prompt turn.

Tier-2..4 (SPEC.md §Submission Protocols) will provide their own
ToolRegistry adapters with different tool surfaces; tier 1's is
[`Tier1ToolRegistry`](../../../src/adapters/tier1_tool_registry.py).

The agent loop is a registry user; it asks the registry for schemas to
advertise on every call and dispatches by name without knowing which
tools exist.
