# `test_when_openhands_solution_generator_constructed_with_model_client_then_default_runner_uses_clients_url_and_key`

Pins the OpenHands SDK wiring entry point per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4. When constructed with a `model_client` and no
`_openhands_runner`, the adapter builds a default runner closure
that — when invoked — would construct an OpenHands `LLM` from
`model_client.base_url` / `.api_key` / `.model_id`.

The actual SDK call is the production binding; the test exercises
the wiring by injecting a fake `_make_runner` factory that
records the model_client and returns a stub runner.

- **Arrange**: a fake `model_client` with `base_url='http://x'`,
  `api_key='k'`, `model_id='m'`. A recording
  `_make_runner(model_client) -> stub_runner` factory.
- **Act**: construct
  `OpenHandsSolutionGenerator(model_client=mc, _make_runner=fake_factory)`;
  call `generate(snapshot)`.
- **Assert**: the factory was called with `mc`; the stub runner
  was called with a prompt containing `snapshot.env_spec`.

Test code: [`../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py`](../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py)::`test_when_openhands_solution_generator_constructed_with_model_client_then_default_runner_uses_clients_url_and_key`.

## Model client injection point

- **Seam**: `_make_runner` factory kwarg.
- **Mode**: **fake** — no OpenHands SDK call, no LLM.

## Runtime scope

> **Runtime scope**: unit only — factory wiring; no SDK import.
