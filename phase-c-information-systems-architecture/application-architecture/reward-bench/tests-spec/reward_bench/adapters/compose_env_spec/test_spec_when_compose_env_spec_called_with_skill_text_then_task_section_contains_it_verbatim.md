# `test_when_compose_env_spec_called_with_skill_text_then_task_section_contains_it_verbatim`

Per §4: the SKILL contract text flows through `compose_env_spec`
unmodified — the agent needs the full FSM contract description.
No paraphrasing or truncation in the composer.

- **Arrange**: `skill_md_text='UNIQUE_TASK_BODY_42'`.
- **Act**: `compose_env_spec(...)`.
- **Assert**: returned string contains `'UNIQUE_TASK_BODY_42'`.

Test code: [`../../../../tests/reward_bench/adapters/test_compose_env_spec.py`](../../../../tests/reward_bench/adapters/test_compose_env_spec.py)::`test_when_compose_env_spec_called_with_skill_text_then_task_section_contains_it_verbatim`.

## Model client injection point

None — pure string composer.

## Runtime scope

> **Runtime scope**: unit only — pure function.
