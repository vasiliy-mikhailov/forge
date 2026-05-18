# `test_when_fake_solution_generator_generate_called_then_returns_scripted_body`

Pins the `FakeSolutionGenerator` shape — the SolutionGenerator
Port's test double per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§2. Used by orchestrator tests and the architecture fitness test
to exercise the role without spawning OpenHands or any LLM.

- **Arrange**: a scripted `body = 'class Solver: pass\n'`. Construct
  `FakeSolutionGenerator(body=body)`. Build a minimal
  `ContextSnapshot`.
- **Act**: `fake.generate(snapshot)`.
- **Assert**: returns the scripted body verbatim.

Test code: [`../../../tests/adapters/test_fake_solution_generator.py`](../../../tests/adapters/test_fake_solution_generator.py)::`test_when_fake_solution_generator_generate_called_then_returns_scripted_body`.

## Model client injection point

- **Seam**: constructor-supplied script.
- **Mode**: **fake** — no real LLM, no IO.

## Runtime scope

> **Runtime scope**: unit only — scripted in-memory adapter.
