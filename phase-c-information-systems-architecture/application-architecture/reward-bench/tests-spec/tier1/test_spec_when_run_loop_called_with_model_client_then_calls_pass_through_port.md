# `test_when_run_loop_called_with_model_client_then_calls_pass_through_port`

Pins the DI seam: when `run_loop(..., model_client=X)`, the loop uses
`X.call()` directly instead of the module-level `_call_model` — no
monkeypatching needed.

## Contract

- **Arrange**: `FakeModelClient(script=({'content': '```tool\n{"name":
  "finish", "args": {"note": "ok"}}\n```', 'tool_calls': []},))`.
  Tmp `workspace/`, `env/`, `tasks/` dirs.
- **Act**: `run_loop(..., model_client=fake, max_iters=3)`.
- **Assert**: the fake's `.calls` list has length ≥ 1 (the loop
  consulted it).

## Model client injection point

- **Seam**: `model_client` constructor arg on `run_loop`.
- **Mode**: fake (`FakeModelClient` explicitly injected).

Test code: [`../../tests/tier1/test_run_loop_di.py`](../../tests/tier1/test_run_loop_di.py)::`test_when_run_loop_called_with_model_client_then_calls_pass_through_port`.

## Runtime scope

> **Runtime scope**: unit only.
