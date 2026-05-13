# `test_when_llm_condenser_compacts_then_summary_appended_to_system_message_and_older_turns_dropped`

Pins the compaction shape of `LlmCondenser`. When the message
history exceeds `1 + keep_recent`, older turns are summarised and
the summary is **appended to the existing system message's
content**, NOT inserted as a separate system message.

Background: cycle 18 pinned the wrong contract — it assumed the
summary becomes a second `role='system'` message at position 1.
Real-system integration with qwen3.6's chat template (vLLM error
`System message must be at the beginning`) rejected that shape.
The fix preserves the one-system-message-at-position-0 invariant
that the chat template enforces.

- **Arrange**: import `LlmCondenser`, `CondenserConfig`. Build a
  7-message history (1 system + 6 turns). Stub `summarise` to
  return `'STUB-SUMMARY of N=K turns'`. `CondenserConfig(
  trigger_tokens=0, keep_recent=2, model_id='qwen3.6-27b-awq')`.
- **Act**: `condenser.condense(messages, config)`.
- **Assert**:
  - `len(result) == 1 + 2` — ONE system message (with summary
    appended) plus the keep_recent window.
  - `result[0]['role'] == 'system'`.
  - The original system content survives in `result[0]['content']`.
  - The stub summary string is also inside `result[0]['content']`.
  - `result[-2:] == messages[-2:]` (keep_recent window preserved).
  - `summarise` was called with the 4 older turns.

Test code: [`tests/reward_bench/adapters/test_llm_condenser.py`](../../../../tests/reward_bench/adapters/test_llm_condenser.py).
