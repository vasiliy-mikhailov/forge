# `test_when_null_condenser_used_then_messages_pass_through_unchanged`

Pins the `CondenserPort` protocol via a null implementation that
simply returns the input messages unchanged. The null-condenser is
the trivial behavior the protocol promises: given messages + config,
return a tuple of messages. The null case is the identity function.

Concrete adapter implementations (LLM-backed summariser) land in
later cycles. This cycle anchors the contract so consumers
(agent_loop integration) can target the port today.

- **Arrange**: import `CondenserPort` (Protocol) and `NullCondenser`
  (a trivial adapter in the same module). Build a 3-message list
  and a `CondenserConfig`.
- **Act**: call `NullCondenser().condense(messages, config)`.
- **Assert**:
  - `NullCondenser` satisfies the `CondenserPort` Protocol (via
    `isinstance(..., CondenserPort)` after `@runtime_checkable`).
  - The returned tuple has the same length as input messages.
  - The returned tuple equals the input messages tuple-converted.

Test code: [`tests/reward_bench/use_cases/test_condenser_port.py`](../../../../tests/reward_bench/use_cases/test_condenser_port.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

