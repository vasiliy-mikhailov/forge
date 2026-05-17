# `src_spec_tier1_tool_registry_advertises_view_execute_submission_finish`
[`Tier1ToolRegistry`](../../../src/adapters/tier1_tool_registry.py) — the
production [`ToolRegistry`](../../../src/ports/tool_registry.py) binding
for tier 1. After the cycle-114 rule-of-three lift, the registry is a
composition of three [`Tool`](../../../src/ports/tool.py) adapters;
per-tool dispatch logic lives in the adapter files, not here.
## Composition
The registry holds a `dict[str, Tool]` over three tier-1 adapters:
| `name` | adapter |
|----------------------|------------------------------------------------------------------------------------------------------------------|
| `view` | [`ViewTool`](../../../src/adapters/tools/view_tool.py) |
| `execute_submission` | [`ExecuteSubmissionTool`](../../../src/adapters/tools/execute_submission_tool.py) |
| `finish` | [`FinishTool`](../../../src/adapters/tools/finish_tool.py) |
`schemas` returns `tuple(t.schema for t in self._tools.values())` —
three OpenAI tool-call definitions, one per adapter.
`dispatch(name, args, ctx)`:
- Looks up `self._tools[name]`; delegates to `tool.dispatch(args, ctx)`.
- Unknown `name`: returns `<error>unknown tool: {name}</error>` (per
 the Tool Port "MUST NOT raise on unknown name" contract).
The registry constructor optionally takes a `tuple[Tool,...]` for
DI; default composition is `(ViewTool(), ExecuteSubmissionTool(),
FinishTool())`.
Tier 2..4 registries will provide different tool surfaces (langgraph,
openhands, orchestrator) per SPEC.md §Submission Protocols, composing
their own Tool adapters under `src/<tier_n>/adapters/tools/`.
