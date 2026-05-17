# `test_when_agent_loop_tool_schemas_imported_then_equals_registry_schemas`

Pins back-compat for the module-level `TOOL_SCHEMAS` export in
`agent_loop.py`. Older callers (and the `_call_model` shim that still
advertises `tools=list(TOOL_SCHEMAS)` to the OpenAI endpoint) read
this re-export instead of constructing the registry themselves;
asserting equality catches drift if either side is ever redefined
independently.

## Contract

- **Arrange**: import `TOOL_SCHEMAS` from `src.tier1.agent_loop` and
  `Tier1ToolRegistry` from `src.adapters.tier1_tool_registry`.
- **Act**: construct a fresh `Tier1ToolRegistry()`.
- **Assert**: `TOOL_SCHEMAS == Tier1ToolRegistry().schemas`.

## Model client injection point

- **Seam**: none — pure import + equality check.
- **Mode**: n/a.

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_agent_loop_tool_schemas_imported_then_equals_registry_schemas`.

## Runtime scope

> **Runtime scope**: unit only — pure module-level export check.
