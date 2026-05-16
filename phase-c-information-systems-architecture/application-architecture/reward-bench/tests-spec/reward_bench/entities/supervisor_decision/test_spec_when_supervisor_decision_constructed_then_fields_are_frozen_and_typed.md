# `test_when_supervisor_decision_constructed_then_fields_are_frozen_and_typed`

Pins the [`SupervisorDecision`](../../../../src-spec/reward_bench/entities/supervisor_decision/src_spec_supervisor_decision.md)
shape per [ADR 0005](../../../../docs/adr/0005-plateau-detection-supervisor-via-llm-self-judgment.md):
the three-field frozen dataclass that the supervisor returns and the
agent_loop hook reads. Three fields, frozen, no IO.

This is a pure-entity test — instantiate, read fields, attempt to
mutate, attempt to construct with wrong types.

- **Arrange**: import `SupervisorDecision`.
- **Act**: construct `SupervisorDecision(plateau=True,
  stop_recommended=False, reasoning='still exploring')`.
- **Assert**:
  - `.plateau is True`, `.stop_recommended is False`,
    `.reasoning == 'still exploring'`.
  - Attempting `decision.plateau = False` raises `FrozenInstanceError`
    (dataclass frozen contract).
  - `plateau` and `stop_recommended` are typed `bool`; `reasoning`
    is typed `str` (no `__annotations__` slip).

Test code: [`tests/reward_bench/entities/test_supervisor_decision.py`](../../../../tests/reward_bench/entities/test_supervisor_decision.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

