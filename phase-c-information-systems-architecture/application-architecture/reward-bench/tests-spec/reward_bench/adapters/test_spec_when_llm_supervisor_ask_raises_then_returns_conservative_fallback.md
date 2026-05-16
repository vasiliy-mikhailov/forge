# `test_when_llm_supervisor_ask_raises_then_returns_conservative_fallback`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

no-silent-fix: ask() throwing must NOT propagate to the agent loop.

## Contract

- **Arrange**: def ask(prompt):; raise ConnectionError('vLLM unreachable'); sweep = ((1, 3000.0, 256, 1.0),)
- **Act**: decision = LlmSupervisor(ask, 'qwen3.6-27b-awq').judge(sweep)
- **Assert**: assert decision.plateau is False; assert decision.stop_recommended is False; assert decision.reasoning.startswith('supervisor parse-error:'), (; f"reasoning was {decision.reasoning!r}"; )

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/reward_bench/adapters/test_llm_supervisor.py`](../../../../tests/reward_bench/adapters/test_llm_supervisor.py)::`test_when_llm_supervisor_ask_raises_then_returns_conservative_fallback`.
