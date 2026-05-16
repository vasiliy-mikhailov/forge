# `test_spec_when_null_condenser_used_then_messages_pass_through_unchanged`

Pins the trivial-condenser contract: every call to
[`NullCondenser`](../../../../src/reward_bench/adapters/null_condenser.py).`condense(messages, config)`
returns `tuple(messages)` unchanged. Also pins
`isinstance(NullCondenser(), CondenserPort) is True` — the test
anchor for runtime-checkable
[Protocol conformance](../../../../src/ports/condenser.py).

Relocated in cycle 116 from
`tests-spec/reward_bench/use_cases/condenser_port/` to mirror the
adapter's new location under `src/reward_bench/adapters/`.

## Contract

- **Arrange**: build a 3-message tuple (system + user + assistant)
  and a `CondenserConfig(trigger_tokens=40000, keep_recent=8,
  model_id='condenser-llama31-8b')`.
- **Act**: call `NullCondenser().condense(messages, config)`.
- **Assert**:
  - `isinstance(condenser, CondenserPort) is True`
  - return is a tuple of length 3
  - return equals input

Test code:
[`tests/reward_bench/adapters/test_null_condenser.py`](../../../../tests/reward_bench/adapters/test_null_condenser.py)::`test_when_null_condenser_used_then_messages_pass_through_unchanged`.

## Model client injection point

- **Seam**: not applicable — NullCondenser takes no model client.
- **Mode**: pure-Python; runs under the default autouse fake binding.
