# `test_when_play_one_game_completes_then_stdout_restored`

Pins stdout restoration AFTER `_play_with_timeout` returns: bench prints issued after the call must be visible normally — the redirection is scoped to the env call only.

## Contract

- **Arrange**: `_PrintingEnv(marker='ignored')`. `capsys` fixture.
- **Act**: `_play_with_timeout(env, solver=None, seed=0, timeout=5)`; then `print('after-play')`.
- **Assert**: `'after-play' in capsys.readouterr().out`.

## Model client injection point

- **Seam**: stdout (verify restored after redirection).
- **Mode**: `@pytest.mark.no_fake`.

Test code: [`../../../tests/tier1/use_cases/test_solver_stdout.py`](../../../tests/tier1/use_cases/test_solver_stdout.py)::`test_when_play_one_game_completes_then_stdout_restored`.

## Runtime scope

> **Runtime scope**: unit only.
