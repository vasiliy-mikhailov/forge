# `test_when_openhands_solution_generator_generate_called_then_runner_receives_prompt_containing_env_spec`

Pins the OpenHands-backed `SolutionGenerator` adapter per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4. The adapter renders a `ContextSnapshot` into a task prompt
and dispatches it to an OpenHands `Conversation`. The actual
OpenHands SDK call is the production binding; tests inject a
recording stub.

The minimum contract pinned here: when `generate(snapshot)` is
called, the injected `_openhands_runner` receives a prompt that
includes `snapshot.env_spec`. The runner's return is the body.

- **Arrange**: a recording stub `_openhands_runner(prompt) -> body`
  that captures the prompt and returns `'class Solver: pass\n'`.
  Build the adapter with the stub injected. Construct a
  `ContextSnapshot` with `env_spec='SPEC: write a Solver'`.
- **Act**: `body = adapter.generate(snapshot)`.
- **Assert**: `'SPEC: write a Solver' in captured_prompt`;
  `body == 'class Solver: pass\n'`.

Test code: [`../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py`](../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py)::`test_when_openhands_solution_generator_generate_called_then_runner_receives_prompt_containing_env_spec`.

## Model client injection point

- **Seam**: `_openhands_runner` constructor kwarg (recording stub).
- **Mode**: **fake** — no OpenHands SDK call.

## Runtime scope

> **Runtime scope**: unit only — prompt-rendering seam test; no OpenHands, no LLM.
