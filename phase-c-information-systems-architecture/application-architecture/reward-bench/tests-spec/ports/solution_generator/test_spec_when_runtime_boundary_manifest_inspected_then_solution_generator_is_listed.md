# `test_when_runtime_boundary_manifest_inspected_then_solution_generator_is_listed`

Pins the §2 `SolutionGenerator` Port registration in the runtime-
boundary architecture manifest per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md).
Registration brings the Port + Fake under ADR-0018's "every
runtime-boundary dependency has Port + production adapter + Fake"
rule. The parametric architecture fitness tests
(`...port_inspected_then_protocol_exists`,
`...port_has_fake_then_fake_class_importable`) auto-extend.

- **Arrange**: locate
  `tests/architecture/test_runtime_boundary_ports.py`.
- **Act**: read the file as text.
- **Assert**: the literal `"SolutionGenerator"` appears.

Test code: [`../../../tests/ports/test_solution_generator.py`](../../../tests/ports/test_solution_generator.py)::`test_when_runtime_boundary_manifest_inspected_then_solution_generator_is_listed`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default).

## Runtime scope

> **Runtime scope**: unit only — text scan of an architecture manifest file.
