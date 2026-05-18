# `test_when_solution_generator_port_inspected_then_generate_takes_snapshot`

Pins the `SolutionGenerator` Port per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§2:

    generate :: ContextSnapshot -> SolverBody

Pure function from a fresh snapshot to a body string. No memory
across calls. The LLM that writes code.

- **Arrange**: import `SolutionGenerator`;
  `inspect.signature(SolutionGenerator.generate)`.
- **Act**: read the parameter names.
- **Assert**: parameter list is exactly `['self', 'snapshot']`.

Test code: [`../../../tests/ports/test_solution_generator.py`](../../../tests/ports/test_solution_generator.py)::`test_when_solution_generator_port_inspected_then_generate_takes_snapshot`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default).

## Runtime scope

> **Runtime scope**: unit only — Protocol method-signature contract.
