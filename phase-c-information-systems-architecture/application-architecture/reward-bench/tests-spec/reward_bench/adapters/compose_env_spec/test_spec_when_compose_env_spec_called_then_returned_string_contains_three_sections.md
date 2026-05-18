# `test_when_compose_env_spec_called_then_returned_string_contains_three_sections`

Per [`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4 binding: env_spec is a self-contained prompt with three named
sections — Task, Dev test harness, Budget. This is the structural
pin: any one of them missing breaks the contract.

- **Arrange**: skill text + an env_py path.
- **Act**: `compose_env_spec(...)`.
- **Assert**: returned string contains `# Task`, `# Dev test
  harness`, and `# Budget` headers.

Test code: [`../../../../tests/reward_bench/adapters/test_compose_env_spec.py`](../../../../tests/reward_bench/adapters/test_compose_env_spec.py)::`test_when_compose_env_spec_called_then_returned_string_contains_three_sections`.

## Model client injection point

None — pure string composer.

## Runtime scope

> **Runtime scope**: unit only — pure function.
