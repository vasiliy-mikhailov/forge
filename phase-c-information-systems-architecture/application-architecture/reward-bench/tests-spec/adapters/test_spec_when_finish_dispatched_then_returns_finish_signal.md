# `test_when_finish_dispatched_then_returns_finish_signal`

Pins the `finish` tool happy-path: with a `note` arg, the dispatcher
returns exactly `'<finish>{note}</finish>'`. The agent loop watches
for this string to terminate.

## Contract

- **Arrange**: any tmp_path (unused by finish).
- **Act**: `Tier1ToolRegistry().dispatch('finish', {'note': 'done'},
  _ctx(tmp_path, tmp_path, tmp_path))`.
- **Assert**: returned string equals `'<finish>done</finish>'`.

## Model client injection point

- **Seam**: none — pure string construction.

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_finish_dispatched_then_returns_finish_signal`.

## Runtime scope

> **Runtime scope**: unit only.
