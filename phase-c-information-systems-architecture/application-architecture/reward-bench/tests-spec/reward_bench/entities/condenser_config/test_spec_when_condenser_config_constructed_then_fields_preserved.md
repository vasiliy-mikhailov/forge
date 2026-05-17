# `test_when_condenser_config_constructed_then_fields_preserved`
Pins the `CondenserConfig` data contract — the orchestrator-side
configuration for the context-compaction step described in SPEC.md
("A condenser summarises older turns when prompt + reserved output
exceeds the budget"). Fields parallel the cycle-21 condenser knobs
(`trigger_tokens`, `keep_recent`, `model_id`) consumed by the active
`LlmCondenser` adapter (per [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
same-model decision).
- **Arrange**: import `CondenserConfig`.
- **Act**: construct `CondenserConfig(trigger_tokens=40000,
 keep_recent=8, model_id='condenser-llama31-8b')`.
- **Assert**: every field reads back its constructor value;
 dataclass is frozen.
Test code: [`tests/reward_bench/entities/test_condenser_config.py`](../../../../tests/reward_bench/entities/test_condenser_config.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.
