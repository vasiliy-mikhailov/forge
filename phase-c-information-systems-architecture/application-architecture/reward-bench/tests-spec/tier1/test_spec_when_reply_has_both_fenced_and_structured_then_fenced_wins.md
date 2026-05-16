# `test_when_reply_has_both_fenced_and_structured_then_fenced_wins`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Cycle 83: fenced format is the default cycle-9/58 protocol;
    structured is purely a fallback when fenced yields zero.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py)::`test_when_reply_has_both_fenced_and_structured_then_fenced_wins`.

## Runtime scope

> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.

