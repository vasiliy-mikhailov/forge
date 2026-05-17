# `src_spec_when_tool_registry_consulted_then_provides_schemas_and_dispatch`

[`ToolRegistry`](../../../src/ports/tool_registry.py) — the
runtime-boundary contract for "advertise the agent's tool surface
and dispatch tool calls". Established by
[ADR 0011](../../../SOLUTION-ARCHITECTURE.md).

Different tiers will provide different registries (tier 1 today;
tier 2-4 future: langgraph, openhands, orchestrator). The agent loop
is a registry **user** — it knows nothing about which tool surface
is in play.

## Types

```python
class ToolContext(TypedDict, total=False):
    workspace: Path
    env_dir: Path
    tasks_dir: Path
    dev_hard_wall_sec: float | None   # per ADR 0006
```

`total=False` — fields are optional; tools ask for what they need
and the registry passes through what it has.

## Contract

```python
class ToolRegistry(Protocol):
    @property
    def schemas(self) -> tuple[dict, ...]: ...

    def dispatch(self, name: str, args: dict, ctx: ToolContext) -> str: ...
```

Semantics:

- `schemas` is the OpenAI tool-call advertisement array passed in
  `ModelClient.call(..., tools=registry.schemas)`. Per
  [ADR 0010](../../../SOLUTION-ARCHITECTURE.md)
  this advertisement is sent on every request.
- `dispatch(name, args, ctx)` runs the named tool and returns the
  observation string that becomes the `role:"tool"` content in the
  next prompt turn.

### Liveness / failure semantics

- **MUST NOT raise on unknown `name`.** Models hallucinate tool
  names; the registry returns an observation string describing the
  protocol violation and lets the agent loop continue.
- **MUST NOT raise on malformed `args`.** Same logic — describe the
  violation in the returned string; the model self-corrects in the
  next iter.
- **MAY raise on infrastructure failure** inside a tool (Docker
  unavailable for `execute_submission`, disk full, etc.). Those are
  bench bugs, not model bugs.

## Adapter manifest

- [`Tier1ToolRegistry`](../../../src/adapters/tier1_tool_registry.py)
  — production tier-1 implementation: `view` + `execute_submission` +
  `finish`. Its src_spec covers the three tool schemas and their
  per-tool args contracts.

Tier-2..4 (SPEC.md §Submission Protocols) will provide their own
ToolRegistry adapters with different tool surfaces.

Enforcement:
[`test_when_runtime_boundary_port_inspected_then_protocol_exists`](../../../tests/architecture/test_runtime_boundary_ports.py)
asserts the Protocol exists; conftest autouse `_bind_tool_registry`
per ADR 0014 binds the production registry as the default test
binding (tier-1 tools are pure and side-effect-free on read-only
paths, so the production registry is also the test default).
