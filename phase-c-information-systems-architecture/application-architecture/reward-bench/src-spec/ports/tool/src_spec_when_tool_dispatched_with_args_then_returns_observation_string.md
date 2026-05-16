# `src_spec_when_tool_dispatched_with_args_then_returns_observation_string`

[`Tool`](../../../src/ports/tool.py) — the runtime-boundary contract
for "a single tool the agent may invoke." Lifted from the
switch-by-name dispatch inside `Tier1ToolRegistry` per the
[CATS rule-of-three](../../../../../../AGENTS.md#lift-implicit-contracts-into-ports--the-rule-of-three)
(three implementations — view, execute_submission, finish — sharing
the same dispatch shape).

## Contract

```python
class Tool(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def schema(self) -> dict: ...

    def dispatch(self, args: dict, ctx: ToolContext) -> str: ...
```

Semantics:

- `name` is the string the model uses to invoke this tool. Matches
  `schema['function']['name']`.
- `schema` is the OpenAI tool-call schema advertised in
  `ModelClient.call(..., tools=[...])` — same shape as a single entry
  in `ToolRegistry.schemas`.
- `dispatch(args, ctx)` runs the tool and returns the observation
  string that becomes the `role:"tool"` content in the next prompt
  turn. `ctx` is the [`ToolContext`](../../../src/ports/tool_registry.py)
  TypedDict (workspace / env_dir / tasks_dir / dev_hard_wall_sec).

### Liveness / failure semantics

- **MUST NOT raise on malformed `args`** — return an `<error>...</error>`
  string instead. Models hallucinate arguments; the agent loop
  self-corrects on the next iter.
- **MAY raise on infrastructure failure** (Docker unavailable for
  ExecuteSubmissionTool, disk full, etc.). Those are bench bugs,
  not model bugs — bubble up.
- **The Port carries no assumption about side effects.** A pure tool
  (FinishTool: returns a formatted string) and a Docker-spawning tool
  (ExecuteSubmissionTool) both satisfy this Port. Per-adapter
  side-effect concerns live in the adapter's own src_spec (or are
  composed in via DI of an underlying Port — e.g.
  ExecuteSubmissionTool wraps `_execute_submission` which itself
  uses ADR-0008 Docker isolation).

## Adapter manifest

Three tier-1 adapters compose the cycle-9/58 tool surface:

- [`ViewTool`](../../../src/adapters/tools/view_tool.py) — reads a
  file from /workspace, /env, or /tasks with `../` escape protection
  and 4000-char trim.
- [`ExecuteSubmissionTool`](../../../src/adapters/tools/execute_submission_tool.py)
  — runs a submission body in the dev sandbox via
  `_execute_submission` (ADR 0008).
- [`FinishTool`](../../../src/adapters/tools/finish_tool.py) — emits
  `<finish>{note}</finish>` to signal end of loop.

Tier 2..4 will compose different sets of Tool adapters per SPEC.md
§Submission Protocols.

Composed by [`Tier1ToolRegistry`](../../../src/adapters/tier1_tool_registry.py)
which holds a `dict[str, Tool]` and dispatches by name lookup with
an "unknown tool" fallback.

Enforcement:
[`test_when_runtime_boundary_port_inspected_then_protocol_exists[Tool]`](../../../tests/architecture/test_runtime_boundary_ports.py)
asserts the Protocol exists.
