# `test_when_canonical_battery_resumes_then_existing_artifacts_skip`

Pins the resume semantics: pre-existing artifact files on disk cause `run_canonical_battery` to SKIP those `(model, trial)` pairs; the runner is invoked only for missing pairs.

## Contract

- **Arrange**: tmp yml with `[alpha, beta]`; pre-write 3 artifact files (alpha trials 0+1, beta trial 0); recorder runner.
- **Act**: `run_canonical_battery(n_trials=3, registry_path=yml, experiments_root=exp, runner=recorder)`.
- **Assert**: only the 3 missing trials invoke the runner: `calls == [('alpha',2),('beta',1),('beta',2)]`.

## Model client injection point

- **Seam**: filesystem (tmp_path) + injected `runner`.
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_resumes_then_existing_artifacts_skip`.

## Runtime scope

> **Runtime scope**: unit only.
