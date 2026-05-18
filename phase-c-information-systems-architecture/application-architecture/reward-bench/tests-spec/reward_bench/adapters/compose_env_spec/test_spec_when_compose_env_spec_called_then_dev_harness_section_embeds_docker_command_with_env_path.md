# `test_when_compose_env_spec_called_then_dev_harness_section_embeds_docker_command_with_env_path`

Per §4: the dev-harness section is an inline shell command the
agent runs via its bash tool. The command must be executable
as-is: absolute host paths are baked in, the image tag is
literal, env vars are set. No path arithmetic at agent runtime.

- **Arrange**: explicit `env_py_path=Path('/abs/tasks/2048/env.py')`,
  `tier1_image='reward-bench-tier1:0.4'`, `dev_games=5`,
  `dev_seed_base=2000`, `dev_timeout_sec=60`.
- **Act**: `compose_env_spec(...)`.
- **Assert**: returned string contains: `docker run`; the env.py
  mount spec with the abs path; the image tag; the
  `REWARD_BENCH_NUM_GAMES=5` and `REWARD_BENCH_SEED_BASE=2000`
  env-var settings; the `timeout 60` prefix.

Test code: [`../../../../tests/reward_bench/adapters/test_compose_env_spec.py`](../../../../tests/reward_bench/adapters/test_compose_env_spec.py)::`test_when_compose_env_spec_called_then_dev_harness_section_embeds_docker_command_with_env_path`.

## Model client injection point

None — pure string composer.

## Runtime scope

> **Runtime scope**: unit only — pure function.
