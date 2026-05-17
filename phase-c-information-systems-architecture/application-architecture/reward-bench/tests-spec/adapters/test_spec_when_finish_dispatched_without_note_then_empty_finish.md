# `test_when_finish_dispatched_without_note_then_empty_finish`

Pins the no-note branch of `finish`: when `args` has no `note` key,
the dispatcher returns `'<finish></finish>'` (empty body, still a
valid finish signal).

## Contract

- **Arrange**: any tmp_path (unused).
- **Act**: `Tier1ToolRegistry().dispatch('finish', {},
  _ctx(tmp_path, tmp_path, tmp_path))`.
- **Assert**: returned string equals `'<finish></finish>'`.

## Model client injection point

- **Seam**: none — pure string construction.

Test code: [`../../tests/adapters/test_tier1_tool_registry.py`](../../tests/adapters/test_tier1_tool_registry.py)::`test_when_finish_dispatched_without_note_then_empty_finish`.

## Runtime scope

> **Runtime scope**: unit only.
