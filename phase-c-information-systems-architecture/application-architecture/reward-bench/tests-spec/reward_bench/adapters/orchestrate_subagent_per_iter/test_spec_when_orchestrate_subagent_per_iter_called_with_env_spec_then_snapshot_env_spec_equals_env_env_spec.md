# `test_when_orchestrate_subagent_per_iter_called_with_env_spec_then_snapshot_env_spec_equals_env_env_spec`

Pins §2 (SOLUTION-ARCHITECTURE.md): the task description lives on
`Env.env_spec`, set by the env_factory at construction; the
orchestrator stamps it verbatim into every per-iter
`ContextSnapshot.env_spec`. Without this the SolutionGenerator
receives an empty task description and has no way to know what to
write.

The test constructs an `Env` with a sentinel `env_spec` string,
runs one iter through `OrchestrateSubagentPerIter` with a
recording generator, and asserts the captured snapshot's
`env_spec` is identical to the env's.

- **Arrange**: recording `SolutionGenerator`; scripted runner;
  `Env(tasks_dir=tmp_path, canonical_scorer=runner,
  env_spec='SENTINEL-TASK-SPEC')`; `BenchConfig(max_iters=1)`.
- **Act**: `list(orch.orchestrate(env, cfg))`.
- **Assert**: `captured[0].env_spec == 'SENTINEL-TASK-SPEC'`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_subagent_per_iter.py`](../../../../tests/reward_bench/adapters/test_orchestrate_subagent_per_iter.py)::`test_when_orchestrate_subagent_per_iter_called_with_env_spec_then_snapshot_env_spec_equals_env_env_spec`.

## Model client injection point

- **Seam**: env's `env_spec` attribute.
- **Mode**: **fake** — no model_client, no SDK.

## Runtime scope

> **Runtime scope**: unit only — single-iter dispatch with a
> recording generator.
