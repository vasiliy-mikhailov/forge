# ADR 0018 — Every runtime-boundary dependency gets a Port, a production adapter, a Fake, and an autouse binding

## Context

The bench has Docker-isolated canonical scoring
([ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md))
plus `ModelClient`, `ToolRegistry`, `ProtocolParser`
([ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md))
and `CpuCountPort`.

`DockerCanonicalScorer` shipped as a concrete class with a duck-typed
`score(...)`. **No Protocol, no Fake, no autouse binding.** `main()`
falls back to constructing a real Docker scorer when `canonical_scorer=`
isn't passed.

Footgun: a test reaching `main()` without explicit injection spawns
Docker in the fast offline gate.

The other three ports have the discipline (conftest autouse
`_bind_model_client` per [ADR 0014](0014-every-test-spec-declares-model-client-injection-point.md)).
Only `DockerCanonicalScorer` escaped it. Codify the pattern so the
next boundary comes with the same shape.

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
(cpu count, env vars), or Docker invocation. Runtime-boundary
dependencies MUST follow this discipline at the moment they're
introduced (the Port comes with the boundary, not later).

Pure-Python composition seams (Callable params in `use_cases/`,
dispatch-by-name registries, single-method shape) are NOT runtime
boundaries — they get lifted to Ports at the **third instance** per
CATS "rule of three". The two rules together cover external
boundaries (forced at first instance) and internal composition (lifted
at third).

## Current manifest

The following ports are tracked under this rule:

| Port | Production | Fake | Autouse binding |
|---|---|---|---|
| `ModelClient` | `VllmOpenAIClient` | `FakeModelClient` | ✓ |
| `ToolRegistry` | `Tier1ToolRegistry` | inline `RecordingRegistry` (tests) | ✓ (via fake_execute_tool) |
| `ProtocolParser` | `CompositeParser([FencedTextParser, StructuredOpenAIParser])` | trivial recorder (tests) | ✓ (via fake_execute_tool) |
| `CpuCountPort` | `MultiprocessingCpuCount` | `FixedCpuCount` | n/a (no side effects; DI param suffices) |
| `CanonicalScorerPort` | `DockerCanonicalScorer` | `FakeCanonicalScorer` | ✓ (cycle 109) |

A port off-manifest is a CATS gap — caught by the architecture test.

## Enforcement

`tests/architecture/test_runtime_boundary_ports.py` asserts:

1. Each manifest port has a `src/ports/<name>.py`.
2. Each has a production adapter under `src/.../adapters/`.
3. Each has a Fake under `src/adapters/fakes/`.
4. Conftest autouse mentions every port needing a default binding.

Manifest is hand-maintained in the architecture test file.

## Consequences

+ New Docker/HTTP/subprocess dependencies are forced to add Port +
  Fake + autouse, or the architecture test fails.
+ Runtime-boundary tests run hermetically by default — no stray Docker
  spawns in the fast gate.
+ Same test_spec serves unit (Fake) and e2e (Live/no_fake) per
  [ADR 0014](0014-every-test-spec-declares-model-client-injection-point.md).
- ~4 small files per dependency instead of 1.
- Hand-maintained manifest can lag; audit cycle is the recourse.

## Path forward

1. `CanonicalScorerPort` Protocol at `src/ports/canonical_scorer.py`.
2. `DockerCanonicalScorer` formally implements it.
3. `InProcessCanonicalScorer` wraps `score_submission` use-case.
4. `FakeCanonicalScorer` returns scripted `AttemptResult`s.
5. Conftest autouse binds the Fake; explicit DI override on `main()`.
6. Architecture test asserts manifest completeness.

## Related

- [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  — first three runtime-boundary ports.
- [ADR 0014](0014-every-test-spec-declares-model-client-injection-point.md)
  — generalises the test_spec injection-point pattern.
