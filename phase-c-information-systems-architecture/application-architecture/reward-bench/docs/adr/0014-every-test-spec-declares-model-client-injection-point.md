# ADR 0014 — Every test_spec declares its ModelClient injection point

## Status

Accepted (cycle 99a). Applies retroactively to all reward-bench
test_specs; pre-cycle-99a specs grandfathered until next touch (no
mass rewrite cycle).

## Context

Two facts about reward-bench tests after cycle 98:

- Most test_specs exercise paths that, somewhere along the call
  chain, end up calling an LLM. Today's bindings call vLLM via
  `_call_model` / `VllmOpenAIClient`. The slow tests can take
  3-30 minutes each.
- After [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  the `ModelClient` is a port with a clear injection seam. An
  in-memory `FakeModelClient` returning scripted replies (per
  [ADR 0012](0012-light-speed-offline-testing-via-injectable-fake-model-client.md))
  exercises the same code path in milliseconds.

The two facts together mean the SAME test_spec can describe both:

- A **unit test** when a `FakeModelClient` is injected — fast,
  hermetic, no GPU.
- An **end-to-end test** when a `VllmOpenAIClient` (or
  `AnthropicClient`, etc.) is injected — slow, real, runs against
  the production stack.

But this requires test_specs to **declare the injection point**
explicitly. A test_spec that says "call `main('qwen3.6-27b-awq')`"
hard-codes the live path. A test_spec that says "call `main(...)`
with a `ModelClient` of the caller's choice" is reusable across
both modes.

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

+ Every existing test_spec gains a clear answer to "where does the
  fake go?" — the question that drove most cycle-78 and cycle-97
  ambiguity.
+ Adding a new test_spec forces the author to think about
  fast-mode coverage before writing slow code.
+ The same test_spec doubles as a unit test (CI/regression gate)
  and an E2E test (live verification of the production stack).
+ Coverage from offline runs approaches live-mode coverage because
  the same tests run in both modes; no separate "fake-only" or
  "live-only" silo.
- Test_specs grow a small fixed section. Worth it for the
  injection-point clarity.
- The conftest autouse fixture is load-bearing; bugs there mask
  real regressions. Mitigated by a meta-test that asserts the
  autouse fixture was applied (cycle 100 candidate).

## Path forward

- **Cycle 99a** (this ADR's implementation):
  - `tests/conftest.py` gains an autouse `FakeVllmInjection`
    fixture, gated on `FAKE_VLLM=1` (default off so live mode
    remains current behaviour).
  - The fixture mocks `_call_model`, `execute_tool`, and
    `ensure_serving_model` for the duration of every test.
  - `FAKE_VLLM=1 pytest tests/ --cov=src` runs the entire suite
    against the fake and reports coverage + runtime.

- **Cycle 100+**: amend each existing test_spec with the
  Model-client-injection-point subsection as it's edited for
  any other reason. No mass-rewrite cycle planned.

## Related

- [ADR 0011](0011-clean-arch-ports-for-model-client-tool-registry-protocol-parser.md)
  — established the `ModelClient` port that makes injection possible.
- [ADR 0012](0012-light-speed-offline-testing-via-injectable-fake-model-client.md)
  — defined the `FakeModelClient` strategy. ADR 0014 mandates
  every test_spec name the seam where the fake plugs in.
- [Forge-wide CATS rule](../../../../phase-preliminary/cats.md#specs-are-language-agnostic)
  — language-agnostic specs. ADR 0014 is the lab-specific
  refinement: this lab's specs ALSO name a model-client injection
  point.
