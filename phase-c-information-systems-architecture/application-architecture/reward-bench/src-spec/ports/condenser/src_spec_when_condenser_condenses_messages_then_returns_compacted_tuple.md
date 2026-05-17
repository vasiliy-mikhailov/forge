# `src_spec_when_condenser_condenses_messages_then_returns_compacted_tuple`

[`CondenserPort`](../../../src/ports/condenser.py) — the
runtime-boundary contract for context-compaction per SPEC.md.

Relocated in cycle 116 from `src/reward_bench/use_cases/condenser_port.py`
to comply with [ADR 0018](../../../SOLUTION-ARCHITECTURE.md)'s
`src/ports/<name>.py` convention.

## Contract

```python
@runtime_checkable
class CondenserPort(Protocol):
    def condense(
        self,
        messages: Tuple[dict, ...],
        config: CondenserConfig,
    ) -> Tuple[dict, ...]: ...
```

Semantics:

- `messages` is an immutable tuple of OpenAI-shape chat messages
  ordered oldest first; position 0 is the system message (chat-template
  invariant — qwen3.6 requires exactly one system message at position 0).
- `config` is a [`CondenserConfig`](../../../src/reward_bench/entities/condenser_config.py)
  carrying `trigger_tokens`, `keep_recent`, and `model_id`.
- Return is a tuple of messages. The last `config.keep_recent` turns
  MUST pass through unchanged. Older turns MAY be compacted into a
  summary appended to the system message.

### Liveness / failure semantics

- **MUST NOT raise.** Failures internal to the adapter (LLM down,
  malformed summary) should degrade to returning `messages`
  unchanged — the agent loop never sees an exception from condensing.
- **Idempotent over identity input.** Calling `condense(messages,
  config)` on already-compacted messages must not further compact.

## Adapter manifest

- [`LlmCondenser`](../../../src/reward_bench/adapters/llm_condenser.py)
  — production adapter. Two gates control firing (both must hold):
  (1) token-gate: `estimated_tokens > trigger_tokens`, where the
  estimate is `sum(len(content) // 4)`; (2) count-gate:
  `len(messages) > 1 + keep_recent`. When firing, older turns
  summarise into a single appended block on the system message.
- [`NullCondenser`](../../../src/reward_bench/adapters/null_condenser.py)
  — trivial adapter; returns `tuple(messages)` unchanged. Default
  when LlmCondenser is not configured. Doubles as the Fake-equivalent
  for tests.

Enforcement:
[`test_when_runtime_boundary_port_inspected_then_protocol_exists[CondenserPort]`](../../../tests/architecture/test_runtime_boundary_ports.py)
asserts the Protocol exists.

## Follow-up: retype run_loop's condense seam

The `condense` parameter in [`run_loop`](../../../src/tier1/agent_loop.py)
is currently `Callable[[Tuple[dict, ...]], Tuple[dict, ...]]` — a
1-arg curried callable rather than a `CondenserPort` instance.
Retyping the seam to accept a `CondenserPort` (and threading
`CondenserConfig` through to the call) is deferred to a separate
cycle per the cycle-113 minimal-implementation discipline.
