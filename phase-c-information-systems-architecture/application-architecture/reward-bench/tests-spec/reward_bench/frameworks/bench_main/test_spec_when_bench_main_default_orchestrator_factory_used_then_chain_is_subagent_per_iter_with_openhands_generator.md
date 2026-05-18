# `test_when_bench_main_default_orchestrator_factory_used_then_chain_is_subagent_per_iter_with_openhands_generator`

Pins the §4 commitment in
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md):
"OpenHands SDK is the committed SolutionGenerator runtime" — at
the production entry point. Calling `bench_main` without an
injected `orchestrator_factory` must wire the §2 three-role chain
`OrchestrateSubagentPerIter(OpenHandsSolutionGenerator(env.model_client),
env.canonical_scorer)`.

The test calls `_default_orchestrator_factory(env)` directly with
a stub env exposing `.model_client` and `.canonical_scorer`,
then inspects the returned orchestrator's private wiring:

- type is `OrchestrateSubagentPerIter`
- `._gen` is an `OpenHandsSolutionGenerator`
- `._runner` is the env's `canonical_scorer`

No SDK calls happen; `OpenHandsSolutionGenerator.__init__` only
constructs a runner closure lazily, so the stub model_client
suffices.

- **Arrange**: stub env with `.model_client` (base_url, api_key,
  model_id attrs) and `.canonical_scorer` sentinel.
- **Act**: `orchestrator = _default_orchestrator_factory(env)`.
- **Assert**: `isinstance(orchestrator, OrchestrateSubagentPerIter)`;
  `isinstance(orchestrator._gen, OpenHandsSolutionGenerator)`;
  `orchestrator._runner is env.canonical_scorer`.

Test code: [`../../../../tests/reward_bench/frameworks/test_bench_main.py`](../../../../tests/reward_bench/frameworks/test_bench_main.py)::`test_when_bench_main_default_orchestrator_factory_used_then_chain_is_subagent_per_iter_with_openhands_generator`.

## Model client injection point

- **Seam**: stub env's `.model_client` attribute.
- **Mode**: **fake** — no SDK calls; `OpenHandsSolutionGenerator`
  lazily wraps the model_client into a runner closure.

## Runtime scope

> **Runtime scope**: unit only — wires the default chain in
> process; the OpenHands SDK is not invoked.
