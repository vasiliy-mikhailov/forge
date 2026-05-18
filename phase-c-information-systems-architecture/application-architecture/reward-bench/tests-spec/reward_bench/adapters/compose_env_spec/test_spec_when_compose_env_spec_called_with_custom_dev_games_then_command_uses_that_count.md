# `test_when_compose_env_spec_called_with_custom_dev_games_then_command_uses_that_count`

Pins `dev_games` parameter wiring into the embedded docker
command. Changing the keyword arg changes the
`REWARD_BENCH_NUM_GAMES=N` env var inside the harness text.

- **Arrange**: `dev_games=20`.
- **Act**: `compose_env_spec(...)`.
- **Assert**: returned string contains `'REWARD_BENCH_NUM_GAMES=20'`.

Test code: [`../../../../tests/reward_bench/adapters/test_compose_env_spec.py`](../../../../tests/reward_bench/adapters/test_compose_env_spec.py)::`test_when_compose_env_spec_called_with_custom_dev_games_then_command_uses_that_count`.

## Model client injection point

None — pure string composer.

## Runtime scope

> **Runtime scope**: unit only — pure function.
