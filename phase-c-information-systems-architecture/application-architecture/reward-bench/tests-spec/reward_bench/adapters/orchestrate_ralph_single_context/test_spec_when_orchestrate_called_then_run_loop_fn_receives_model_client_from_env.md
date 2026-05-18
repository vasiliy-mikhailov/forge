# `test_when_orchestrate_called_then_run_loop_fn_receives_model_client_from_env`

Pins the §7 ralph adapter env→run_loop pass-through for
`model_client`. `run_loop`'s signature already accepts
`model_client=` as a kwarg, so no further wrapper work is needed —
the adapter just forwards `env.model_client`.

- **Arrange**: `fake_mc = object()` sentinel;
  `env = Env(tasks_dir=tmp_path, canonical_scorer=fake_scorer,
  model_client=fake_mc)`; recording fake run_loop; adapter with
  the fake.
- **Act**: `list(adapter.orchestrate(env, cfg))`.
- **Assert**: `captured['model_client'] is fake_mc`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_orchestrate_called_then_run_loop_fn_receives_model_client_from_env`.

## Model client injection point

- **Seam**: `run_loop_fn` constructor parameter (recording fake).
- **Mode**: **fake** — captures kwargs without spawning anything.

## Runtime scope

> **Runtime scope**: unit only — kwarg pass-through; no real loop.
