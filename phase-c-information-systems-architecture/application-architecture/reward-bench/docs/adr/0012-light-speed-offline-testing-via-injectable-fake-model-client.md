# ADR 0012 — Light-speed offline testing via injectable `FakeModelClient`

## Status

Accepted (cycle 98). Implementation lands in cycle 99 once
[ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
step 2 (run_loop takes the ports as DI params) is in place.

## Context

The smoke v2 sweep (cycles 78 + 97) takes ~30 minutes per model
× 22 models = up to 12 hours wall time. Most of that is vLLM
container provisioning + model loading + inference — none of
which exercises the bench's own logic.

After ADR 0011 (cycles 98a–c) the bench loop talks to three
ports:
  - `ModelClient` — sends `messages` + `tools` to a model server,
    returns `AssistantReply`.
  - `ToolRegistry` — dispatches `(name, args, ctx)` to tool handlers.
  - `ProtocolParser` — turns `AssistantReply` into `ToolCall`s.

The model client is the single chokepoint where the GPU/vLLM lives.
A test that swaps `VllmOpenAIClient` for an in-memory fake gets
**identical bench behavior** without any of the cost.

## Decision

Add a `FakeModelClient(ModelClient)` adapter under
`src/adapters/fakes/`. The adapter takes a list of scripted
`AssistantReply` values at construction and returns them in order.
Tests parametrise over `MODEL_REGISTRY` (so coverage stays honest)
but every iteration uses the same fake client — the `model_id`
parameter is logged, not honored, since there's no real inference.

A new `tests/reward_bench/frameworks/smoke/test_smoke_fast.py`
becomes the canonical "is the bench loop healthy?" check:
  - One script per scenario (happy-path Solver, regress-then-restore,
    no-tool prose, ...) — each is a tuple of `AssistantReply`s.
  - 22 model IDs × 5 scenarios = 110 tests, all running in seconds.
  - Replaces the cycle-78 smoke v2 sweep as the CI gate.

The slow vLLM-backed smoke (current `test_smoke_all_models.py`)
becomes an opt-in *live* gate, run on demand to validate that
real model output is still bench-compatible. The fast smoke is
the default.

## Consequences

+ CI/regression turnaround: ~3 seconds for the full bench-logic
  coverage instead of 30 min/model.
+ Bench bugs land in fast smoke before they reach a GPU run.
+ Scenarios (regress-then-restore, no-tool-stall, walltime_exceeded
  cascade) become reproducible artefacts, not "we'll see if a model
  triggers it" leaderboard footnotes.
+ Bench cycles (cycles 98+, ADR 0011 follow-ups) no longer pay
  GPU minutes for verification.
- Fast smoke does NOT test the vLLM serving stack, the tool-call
  parser config, or the docker layer. Those need their own targeted
  live tests (one per concern, not one per model).

## Path forward

**Cycle 99** (preceding this): wire `run_loop(*, model_client,
tool_registry, protocol_parser, ...)` so callers pass the triple.

**Cycle 99a** (this ADR's implementation):
  - Add `src/adapters/fakes/fake_model_client.py`.
  - Add `src/adapters/fakes/scripts.py` with 5 reference scripts
    (happy / regress / no-tool / walltime / protocol-violation).
  - Add `tests/reward_bench/frameworks/smoke/test_smoke_fast.py`
    parametrized over MODEL_REGISTRY × scripts.
  - Mark `test_smoke_all_models.py` with `@pytest.mark.live` so
    `pytest -m 'not live'` runs only the fast variant by default.

**Cycle 99b** (after fast smoke proven): retire cycle-78 / cycle-97
artefacts to `experiments/archive/` and document the fast-smoke
artefact as the new leaderboard substrate.

## Related

- [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  — established the ports this ADR exploits.
- [ADR 0009](0009-multi-model-smoke-bench-convention.md)
  — the smoke convention being tested. Fast smoke does NOT replace
  this; it accelerates verifying it.
