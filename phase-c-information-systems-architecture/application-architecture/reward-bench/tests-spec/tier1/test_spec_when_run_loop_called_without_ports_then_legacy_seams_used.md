# `test_when_run_loop_called_without_ports_then_legacy_seams_used`

Pins back-compat: pre-port callers that pass no `model_client`,
`tool_registry`, or `protocol_parser` still go through the
module-level `_call_model` / `execute_tool` / `parse_tool_calls`,
so existing monkeypatching tests stay green.

## Contract

- **Arrange**: monkeypatch `src.tier1.agent_loop._call_model` with a
  fake that returns a fenced `finish` call and increments a counter.
  Tmp `workspace/`, `env/`, `tasks/` dirs.
- **Act**: `al.run_loop(..., max_iters=3)` — **no** port kwargs.
- **Assert**: the fake `_call_model` was invoked at least once
  (`fake_call_count['n'] >= 1`).

## Model client injection point

- **Seam**: module-level `_call_model` (legacy, monkeypatched).
- **Mode**: fake.

Test code: [`../../tests/tier1/test_run_loop_di.py`](../../tests/tier1/test_run_loop_di.py)::`test_when_run_loop_called_without_ports_then_legacy_seams_used`.

## Runtime scope

> **Runtime scope**: unit only.
