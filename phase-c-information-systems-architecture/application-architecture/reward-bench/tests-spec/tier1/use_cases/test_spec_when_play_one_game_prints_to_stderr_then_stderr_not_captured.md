# `test_when_play_one_game_prints_to_stderr_then_stderr_not_captured`

Pins the stderr-redirection contract: `print(..., file=sys.stderr)` inside the env's call path MUST NOT leak to the bench process's stderr (same flooding concern as stdout).

## Contract

- **Arrange**: `_PrintingEnv(marker='solver-stderr-marker', to_stderr=True)`. `capsys` fixture.
- **Act**: `_play_with_timeout(env, solver=None, seed=0, timeout=5)`.
- **Assert**: `'solver-stderr-marker' not in capsys.readouterr().err`.

## Model client injection point

- **Seam**: stderr (redirected).
- **Mode**: `@pytest.mark.no_fake`.

Test code: [`../../../tests/tier1/use_cases/test_solver_stdout.py`](../../../tests/tier1/use_cases/test_solver_stdout.py)::`test_when_play_one_game_prints_to_stderr_then_stderr_not_captured`.

## Runtime scope

> **Runtime scope**: unit only.
