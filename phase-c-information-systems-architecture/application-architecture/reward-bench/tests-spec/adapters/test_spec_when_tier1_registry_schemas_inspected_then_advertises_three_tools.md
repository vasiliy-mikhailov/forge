# `test_when_tier1_registry_schemas_inspected_then_advertises_three_tools`

Pins the tier-1 tool catalogue: `Tier1ToolRegistry().schemas` is a
tuple of exactly three OpenAI tool schemas — `view`,
`execute_submission`, `finish` — each with `type='function'`.

## Contract

- **Arrange**: `registry = Tier1ToolRegistry()`.
- **Act**: `schemas = registry.schemas`.
- **Assert**: `len(schemas) == 3`; names extracted from
  `s['function']['name']` form the set `{'view',
  'execute_submission', 'finish'}`; every `s['type'] == 'function'`.

## Model client injection point

- **Seam**: none — pure constructor + attribute read.

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_tier1_registry_schemas_inspected_then_advertises_three_tools`.

## Runtime scope

> **Runtime scope**: unit only.
