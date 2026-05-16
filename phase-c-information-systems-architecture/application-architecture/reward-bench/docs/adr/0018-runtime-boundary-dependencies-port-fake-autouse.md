# ADR 0018 — Every runtime-boundary dependency gets a Port, a production adapter, a Fake, and an autouse binding

## Context

After cycle 105 the bench has Docker-isolated canonical scoring
([ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md))
plus three previously-extracted ports — `ModelClient`, `ToolRegistry`,
`ProtocolParser` ([ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md))
— and a fourth small one for cpu count.

The cycle 105 Docker work shipped `DockerCanonicalScorer` as a
concrete class with a duck-typed `score(...)` method. There is **no
Protocol**, **no in-memory Fake**, and **no autouse binding** in the
test conftest. `main()` accepts an optional `canonical_scorer=`
parameter and falls back to constructing the real `DockerCanonicalScorer`
when none is provided.

This creates a footgun: any test reaching `main()` without explicitly
passing a `canonical_scorer=` argument will attempt to spawn a Docker
container in the fast offline gate. Today no test trips this (the
cycle-105 sub-C tests explicitly inject; older tests are
`@pytest.mark.live`), but the next author will.

We already have the discipline for the other three ports: the conftest
autouse `_bind_model_client` fixture (cycle 99a / [ADR 0014](0014-every-test-spec-declares-model-client-injection-point.md))
intercepts `_call_model`, `urlopen`, `execute_tool`, and
`ensure_serving_model`. The pattern is right; only `DockerCanonicalScorer`
escaped it.

The opportunity: codify the pattern explicitly so the next runtime-boundary
dependency comes with the same shape automatically.

## Decision

**Every dependency that crosses a runtime boundary MUST be wired
through a Port and have four artifacts**:

1. **Port** — a `Protocol` class under `src/ports/<name>.py` declaring
   the public surface. Type signature is the contract; the prose-only
   spec lives in `src-spec/ports/<name>/`.
2. **Production adapter(s)** — under `src/adapters/` or
   `src/<module>/adapters/` depending on cross-cutting vs module-local
   scope. Implements the Port.
3. **Fake adapter** — under `src/adapters/fakes/<name>.py`.
   In-memory; deterministic; ignores side effects. Production adapters
   never go through the Fake; the Fake is purely for tests.
4. **Autouse binding** — `tests/conftest.py` autouse fixture binds the
   Fake when the test isn't marked `live` (real production stack) or
   `no_fake` (real production code under hermetic local sandbox).
   Tests that want a specific scripted instance pass it explicitly via
   the DI parameter.

A "runtime boundary" is one of: subprocess shell-out, HTTP/network
call, file-system path that depends on host state, OS process state
(cpu count, env vars), or Docker invocation. Pure-Python code without
side effects does NOT need this treatment.

## Current manifest

The following ports are tracked under this rule:

| Port | Production | Fake | Autouse binding |
|---|---|---|---|
| `ModelClient` | `VllmOpenAIClient` | `FakeModelClient` | ✓ |
| `ToolRegistry` | `Tier1ToolRegistry` | inline `RecordingRegistry` (tests) | ✓ (via fake_execute_tool) |
| `ProtocolParser` | `CompositeParser([FencedTextParser, StructuredOpenAIParser])` | trivial recorder (tests) | ✓ (via fake_execute_tool) |
| `CpuCountPort` | `MultiprocessingCpuCount` | `FixedCpuCount` | n/a (no side effects; DI param suffices) |
| `CanonicalScorerPort` | `DockerCanonicalScorer` | `FakeCanonicalScorer` | ✓ (cycle 109) |

Adding a port that ISN'T on this manifest is a CATS gap — the
architecture test will catch it on the next pass.

## Enforcement

`tests/architecture/test_runtime_boundary_ports.py` asserts:

1. Each port name in the manifest above has a `src/ports/<name>.py` (or
   the legacy location like `src/ports/cpu_count.py`).
2. Each port has at least one production adapter implementing it
   (heuristically: a class under `src/.../adapters/` whose name
   matches `<X>Client`, `<X>Scorer`, `<X>Registry`, `<X>Parser`,
   `<X>Provisioner`, etc., and whose source mentions the port name).
3. Each port has a Fake adapter under `src/adapters/fakes/`.
4. The conftest autouse fixture mentions every port that needs a
   default-bound instance.

Failure of any check is a test failure. The manifest is a
hand-maintained list in the architecture test file — new ports get
added there alongside their first src-spec.

## Consequences

+ The next author who introduces a Docker / HTTP / subprocess
  dependency is forced to add Port + Fake + autouse, or the
  architecture test fails.
+ Tests that touch any runtime-boundary code are guaranteed to run
  hermetically by default — no surprises like a stray Docker spawn
  during the fast gate.
+ Same test_spec can serve as unit (Fake binding) AND e2e (Live or
  no_fake binding) — per [ADR 0014](0014-every-test-spec-declares-model-client-injection-point.md)
  the test_spec names the seam, and the conftest does the binding.
- New runtime-boundary dependencies cost ~4 small files instead of 1.
  Marginal up-front; pays off the second time a test wedges.
- The manifest is a hand-maintained list. If someone adds a port
  without registering it in the manifest, the architecture test
  doesn't catch the gap. Mitigated by: the audit cycle that produced
  this ADR is the standard recourse.

## Path forward (cycle 109)

1. Add `CanonicalScorerPort` Protocol under `src/ports/canonical_scorer.py`.
2. Make `DockerCanonicalScorer` formally implement it (no runtime
   change; just an inheritance declaration + type check).
3. Wrap the in-process `score_submission` use-case in
   `InProcessCanonicalScorer` adapter for parity (Layer 1 fallback).
4. Add `FakeCanonicalScorer` returning scripted `AttemptResult`s.
5. Conftest autouse binds the Fake by default; explicit DI parameter
   on `main()` overrides.
6. Architecture test asserts the manifest is complete.

## Related

- [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  — the first three runtime-boundary ports.
- [ADR 0014](0014-every-test-spec-declares-model-client-injection-point.md)
  — test_specs name the injection point; ADR 0018 generalises the
  pattern to non-model-client boundaries.
- Cycle 105 — `DockerCanonicalScorer` shipped without the full
  pattern; cycle 109 closes the gap and codifies the rule.
