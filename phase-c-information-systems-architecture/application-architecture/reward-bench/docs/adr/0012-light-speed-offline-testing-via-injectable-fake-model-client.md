# ADR 0012 — Light-speed offline testing via injectable `FakeModelClient`

## Status

Accepted (cycle 98). Implementation lands in cycle 99 once
[ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
step 2 (run_loop takes the ports as DI params) is in place.

## Context

The smoke v2 sweep takes ~30 min/model × 22 models = up to 12 h wall.
Mostly vLLM provisioning + model loading + inference — none of which
exercises bench logic.

After ADR 0011 the loop talks to three ports: `ModelClient`,
`ToolRegistry`, `ProtocolParser`. The model client is the GPU/vLLM
chokepoint. Swapping `VllmOpenAIClient` for an in-memory fake gets
**identical bench behavior** without the cost.

## Decision

Add `FakeModelClient(ModelClient)` at `src/adapters/fakes/`. Takes a
list of scripted `AssistantReply` at construction; returns them in
order. Tests parametrise over `MODEL_REGISTRY` for coverage; `model_id`
is logged, not honoured.

New `tests/reward_bench/frameworks/smoke/test_smoke_fast.py` is the
canonical "is the bench loop healthy?" check:

- One script per scenario (happy / regress-then-restore / no-tool /
  walltime / protocol-violation).
- 22 models × 5 scenarios = 110 tests in seconds.
- Replaces the smoke v2 sweep as the CI gate.

The vLLM-backed `test_smoke_all_models.py` becomes opt-in *live*,
run on demand.

## Consequences

+ CI turnaround ~3 s for full bench-logic coverage vs 30 min/model.
+ Bench bugs land in fast smoke before any GPU run.
+ Scenarios become reproducible artefacts, not leaderboard footnotes.
+ Verification cycles no longer pay GPU minutes.
- Fast smoke does NOT cover the vLLM stack, parser config, or docker
  layer. Those need targeted live tests (one per concern).

## Path forward

1. Wire `run_loop(*, model_client, tool_registry, protocol_parser, ...)`.
2. Add `fake_model_client.py` + 5 reference scripts + `test_smoke_fast.py`
   parametrized over MODEL_REGISTRY × scripts. Mark
   `test_smoke_all_models.py` `@pytest.mark.live`.
3. After fast smoke proven, retire old artefacts to
   `experiments/archive/`.

## Related

- [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  — ports this ADR exploits.
- [ADR 0009](0009-multi-model-smoke-bench-convention.md) — smoke
  convention being verified.
