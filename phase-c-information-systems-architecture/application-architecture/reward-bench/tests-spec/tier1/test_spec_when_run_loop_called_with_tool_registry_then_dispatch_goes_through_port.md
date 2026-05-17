# `test_when_run_loop_called_with_tool_registry_then_dispatch_goes_through_port`

Pins the DI seam for `ToolRegistry`: when `run_loop(...,
tool_registry=R)`, `R.dispatch()` handles tool calls instead of the
module-level `execute_tool`.

## Contract

- **Arrange**: a `RecordingRegistry(ToolRegistry)` whose `schemas`
  mirrors prod and whose `dispatch` records `(name, args)` tuples
  into a list; returns `<finish>ok</finish>` for `'finish'` calls.
  `FakeModelClient` scripted to emit one fenced `finish` call.
- **Act**: `run_loop(..., model_client=fake, tool_registry=registry,
  max_iters=3)`.
- **Assert**: `registry.dispatched` has the recorded `'finish'` call.

## Model client injection point

- **Seam**: `tool_registry` constructor arg on `run_loop`.
- **Mode**: fake (recording registry explicitly injected).

Test code: [`../../tests/tier1/test_run_loop_di.py`](../../tests/tier1/test_run_loop_di.py)::`test_when_run_loop_called_with_tool_registry_then_dispatch_goes_through_port`.

## Runtime scope

> **Runtime scope**: unit only.
