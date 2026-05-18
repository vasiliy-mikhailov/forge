# `test_when_default_run_loop_fn_invoked_with_model_client_having_url_attrs_then_vllm_kwargs_supplied`

Pins the §7 wrapper's URL extraction per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
`run_loop` requires `vllm_base_url`, `vllm_api_key`, `model_id` as
positional/required kwargs even when a pre-bound `model_client` is
supplied. The wrapper bridges this: when `model_client` exposes
the three URL attributes, the wrapper derives the legacy kwargs
from them.

- **Arrange**: inline `MockClient` with attributes
  `base_url='http://my-vllm:8000'`, `api_key='secret'`,
  `model_id='m-42'`; `fake_inner_run_loop` capturing kwargs;
  `fn = default_run_loop_fn(_run_loop=fake_inner, _time_fn=lambda: 0.0)`.
- **Act**: `fn(model_client=MockClient())` (no explicit URL kwargs).
- **Assert**: `captured['vllm_base_url'] == 'http://my-vllm:8000'`
  AND `captured['vllm_api_key'] == 'secret'` AND
  `captured['model_id'] == 'm-42'`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_default_run_loop_fn_invoked_with_model_client_having_url_attrs_then_vllm_kwargs_supplied`.

## Model client injection point

- **Seam**: `_run_loop` keyword (recording fake) + inline mock for
  `model_client`.
- **Mode**: **fake** — no real client, no real loop.

## Runtime scope

> **Runtime scope**: unit only — wrapper attribute extraction; no real loop.
