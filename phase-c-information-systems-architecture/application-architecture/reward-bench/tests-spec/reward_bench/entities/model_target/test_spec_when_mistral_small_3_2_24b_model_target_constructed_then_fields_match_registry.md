# `test_when_mistral_small_3_2_24b_model_target_constructed_then_fields_match_registry`
Pins one candidate model — `mistral-small-3.2-24b` — as a concrete
`ModelTarget`. The values mirror the entry in
`phase-c-information-systems-architecture/application-architecture/wiki-compiler/configs/models.yml`.
A drift between this test and the registry surfaces immediately.
- **Arrange**: import `ModelTarget` from
 `src.reward_bench.entities.model_target`.
- **Act**: construct
 `ModelTarget(id='mistral-small-3.2-24b',
 hf_path='RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4',
 served_name='mistral-small-3.2-24b',
 max_model_len=131072,
 tool_call_parser='mistral')`.
- **Assert**: every field reads back exactly the value it was
 constructed with. The dataclass is frozen, so attempted mutation
 would raise `FrozenInstanceError`.
This test is the bench's first **multi-model** test spec. Mistral
exercises generality versus the qwen3.6 baseline: different family,
different tool parser, no reasoning parser, no `enable_thinking`
gate.
Test code: [`tests/reward_bench/entities/test_model_target.py`](../../../tests/reward_bench/entities/test_model_target.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.
