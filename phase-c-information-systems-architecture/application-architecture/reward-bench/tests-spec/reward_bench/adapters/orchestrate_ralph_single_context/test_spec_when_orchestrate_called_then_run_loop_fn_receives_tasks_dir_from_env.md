# `test_when_orchestrate_called_then_run_loop_fn_receives_tasks_dir_from_env`

Pins the first kwarg pass-through of the §7 ralph adapter per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
The real `src.tier1.agent_loop.run_loop` requires `tasks_dir`
among other kwargs; `orchestrate(env, cfg)` must extract it from
`env` and thread it through `run_loop_fn`. Without this, the
production binding crashes on the very first call.

- **Arrange**: `tmp_path` as tasks_dir; `env = Env(tasks_dir=tmp_path,
  canonical_scorer=FakeCanonicalScorer())`; a recording
  `fake_run_loop` that stashes its kwargs into a dict; adapter
  constructed with this fake.
- **Act**: `list(adapter.orchestrate(env, cfg))`.
- **Assert**: `captured['tasks_dir'] == tmp_path`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_orchestrate_called_then_run_loop_fn_receives_tasks_dir_from_env`.

## Model client injection point

- **Seam**: `run_loop_fn` constructor parameter (recording fake).
- **Mode**: **fake** — captures kwargs without spawning anything.

## Runtime scope

> **Runtime scope**: unit only — kwarg pass-through; no real loop.
