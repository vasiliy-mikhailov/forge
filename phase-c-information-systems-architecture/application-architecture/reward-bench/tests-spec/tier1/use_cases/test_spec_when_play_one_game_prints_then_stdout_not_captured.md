# `test_when_play_one_game_prints_then_stdout_not_captured`

Pins the stdout-redirection contract: `print()` issued inside the env's call path during `_play_with_timeout` MUST NOT leak to the bench process's stdout (would flood the bench log).

## Contract

- **Arrange**: `_PrintingEnv(marker='solver-stdout-marker')` that prints the marker during `play_one_game`. `capsys` fixture.
- **Act**: `_play_with_timeout(env, solver=None, seed=0, timeout=5)`.
- **Assert**: `result.score == 42`; `'solver-stdout-marker' not in capsys.readouterr().out`.

## Model client injection point

- **Seam**: stdout (redirected by `_play_with_timeout`).
- **Mode**: `@pytest.mark.no_fake` — real `_play_with_timeout` code, synthetic env.

Test code: [`../../../tests/tier1/use_cases/test_solver_stdout.py`](../../../tests/tier1/use_cases/test_solver_stdout.py)::`test_when_play_one_game_prints_then_stdout_not_captured`.

## Runtime scope

> **Runtime scope**: unit only.
