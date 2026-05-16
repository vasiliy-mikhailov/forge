# `test_when_structured_arguments_contains_sentencepiece_space_then_stripped_before_parsing`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Cycle 96: vLLM mistral tokenizer leaks U+0120 / U+2581 into the
    rendered JSON arguments. parse_tool_calls must strip them so
    json.loads succeeds.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py)::`test_when_structured_arguments_contains_sentencepiece_space_then_stripped_before_parsing`.

## Runtime scope

> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.

