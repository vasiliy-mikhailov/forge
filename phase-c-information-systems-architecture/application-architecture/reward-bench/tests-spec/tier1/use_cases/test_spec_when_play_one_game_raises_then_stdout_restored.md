# `test_when_play_one_game_raises_then_stdout_restored`

Pins defensive stdout restoration on the exception path: when the env raises during `_play_with_timeout`, stdout MUST still be restored — no permanent redirection leak.

## Contract

- **Arrange**: `_PrintingEnv(marker='ignored', raises=RuntimeError('boom'))`. `capsys` fixture.
- **Act**: `_play_with_timeout(env, ..., timeout=5)` inside `pytest.raises(RuntimeError)`; then `print('after-raise')`.
- **Assert**: the raise happens AND `'after-raise' in capsys.readouterr().out`.

## Model client injection point

- **Seam**: stdout (verify restored on exception).
- **Mode**: `@pytest.mark.no_fake`.

Test code: [`../../../tests/tier1/use_cases/test_solver_stdout.py`](../../../tests/tier1/use_cases/test_solver_stdout.py)::`test_when_play_one_game_raises_then_stdout_restored`.

## Runtime scope

> **Runtime scope**: unit only.
