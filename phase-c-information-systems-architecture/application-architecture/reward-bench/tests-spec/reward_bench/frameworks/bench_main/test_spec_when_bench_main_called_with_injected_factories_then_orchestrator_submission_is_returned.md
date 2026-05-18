# `test_when_bench_main_called_with_injected_factories_then_orchestrator_submission_is_returned`

Pins the §7 production binding per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
`bench_main` is the thin composition that the production CLI calls:
it takes a `ModelTarget` and `BenchConfig`, builds an `Env` via
`env_factory(target)`, constructs an `Orchestrator` via
`orchestrator_factory(env)`, calls `bench(orchestrator, env, cfg)`,
returns the resulting `Submission`.

Both factories are injectable so tests pin the composition without
spawning Docker or vLLM. The defaults wire the
`OrchestrateSubagentPerIter(OpenHandsSolutionGenerator(env.model_client),
env.canonical_scorer)` chain and a real `Env` (Docker scorer +
VllmOpenAIClient + repo tasks dir).

`orchestrator_factory` receives `env` so it can read
`env.model_client` (for the SolutionGenerator) and
`env.canonical_scorer` (for the Runner) without bench_main having
to thread those through.

- **Arrange**: a `ModelTarget` sentinel; a fake `env_factory` that
  asserts it was called with that target and returns a sentinel
  env; a fake `orchestrator_factory` that asserts it was called
  with that env and returns
  `FakeOrchestrator(submissions=(expected,))`; `BenchConfig()`.
- **Act**: `bench_main(target, cfg, env_factory=fake_env_factory,
  orchestrator_factory=fake_orch_factory)`.
- **Assert**: returns `expected` (the scripted Submission); the
  env captured by orchestrator_factory is the one env_factory
  produced.

Test code: [`../../../../tests/reward_bench/frameworks/test_bench_main.py`](../../../../tests/reward_bench/frameworks/test_bench_main.py)::`test_when_bench_main_called_with_injected_factories_then_orchestrator_submission_is_returned`.

## Model client injection point

- **Seam**: `env_factory` keyword (returns Env including model_client).
- **Mode**: **fake** — both factories injected; no real infra.

## Runtime scope

> **Runtime scope**: unit only — pure composition test with two injected factories; no Docker, no vLLM.
