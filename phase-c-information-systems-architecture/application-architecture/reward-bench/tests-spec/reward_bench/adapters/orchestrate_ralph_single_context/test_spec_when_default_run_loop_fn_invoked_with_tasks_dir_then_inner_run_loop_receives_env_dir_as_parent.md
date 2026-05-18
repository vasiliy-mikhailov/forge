# `test_when_default_run_loop_fn_invoked_with_tasks_dir_then_inner_run_loop_receives_env_dir_as_parent`

Pins the §7 wrapper's `env_dir` derivation per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
`env_dir` is a derived path (the parent of `tasks_dir`); it does
not belong in the adapter API any more than `workspace` does. The
production wrapper computes it.

Mirrors existing `main.py` derivation: `ENV_DIR = TASKS_DIR.parent`.

- **Arrange**: `fake_inner_run_loop` capturing kwargs;
  `fn = default_run_loop_fn(_run_loop=fake, _time_fn=lambda: 0.0)`.
- **Act**: `fn(tasks_dir=Path('/x/y/z'))`.
- **Assert**: `captured['env_dir'] == Path('/x/y')`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_default_run_loop_fn_invoked_with_tasks_dir_then_inner_run_loop_receives_env_dir_as_parent`.

## Model client injection point

- **Seam**: `_run_loop` keyword (recording fake).
- **Mode**: **fake** — captures kwargs without spawning anything.

## Runtime scope

> **Runtime scope**: unit only — pure path derivation in the wrapper.
