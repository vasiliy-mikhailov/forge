# ADR 0014 — Every test_spec declares its ModelClient injection point

## Status

Accepted (cycle 99a). Applies retroactively to all reward-bench
test_specs; pre-cycle-99a specs grandfathered until next touch (no
mass rewrite cycle).

## Context

Two facts:

- Most test_specs end up calling an LLM via `_call_model` /
  `VllmOpenAIClient`. Slow tests take 3-30 minutes.
- After [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  `ModelClient` is a port. A `FakeModelClient` (per
  [ADR 0012](0012-light-speed-offline-testing-via-injectable-fake-model-client.md))
  runs the same code path in milliseconds.

The same test_spec can describe both modes — unit (fake injected) and
end-to-end (live client injected) — but only if it **declares the
injection point** explicitly. "Call `main('qwen3.6-27b-awq')`"
hard-codes live; "call `main(...)` with a `ModelClient` of caller's
choice" is reusable.

## Decision

Every reward-bench test_spec MUST include a **Model client
injection point** subsection that names:

1. The seam where the `ModelClient` enters the test
   (e.g. "`run_loop(model_client=...)`",
   "autouse `conftest.py` fixture replaces `_call_model`",
   "constructor arg on the use-case under test").
2. The default fixture mode: `fake` (unit) or `live` (e2e).
3. The mechanism for swapping the other direction (env var,
   pytest marker, fixture override).

Example test_spec subsection (canonical phrasing):

> ## Model client injection point
>
> - **Seam**: `run_loop(model_client=...)` (or pre-cycle-99 the
>   `_call_model` shim in `agent_loop.py`).
> - **Default**: `fake` — `tests/conftest.py` autouse fixture
>   installs a `FakeModelClient` returning the script described in
>   the test's Arrange step.
> - **Live override**: run with `FAKE_VLLM=0 pytest -m live tests/…`
>   to swap in `VllmOpenAIClient` and exercise the same assertions
>   end-to-end.

A test_spec without this subsection is incomplete after cycle 99a
and should be amended before adding behaviour to the test.

## Consequences

+ Every test_spec answers "where does the fake go?".
+ New specs force the author to think about fast-mode coverage.
+ Same test_spec doubles as unit test (CI gate) and E2E (live verify).
+ Offline coverage approaches live coverage — no fake-only or
  live-only silos.
- Test_specs grow a small fixed section.
- The conftest autouse fixture is load-bearing; mitigated by a
  meta-test asserting it was applied.

## Path forward

- `tests/conftest.py` gains an autouse `FakeVllmInjection` fixture
  gated on `FAKE_VLLM=1` (default off). Mocks `_call_model`,
  `execute_tool`, `ensure_serving_model`.
- `FAKE_VLLM=1 pytest tests/ --cov=src` runs the suite against fakes.
- Existing test_specs amended as they're edited; no mass rewrite.

## Related

- [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  — the `ModelClient` port.
- [ADR 0012](0012-light-speed-offline-testing-via-injectable-fake-model-client.md)
  — the `FakeModelClient` strategy.
- [Forge-wide CATS rule](../../../../phase-preliminary/cats.md#specs-are-language-agnostic)
  — language-agnostic specs; this is the lab-specific refinement.
