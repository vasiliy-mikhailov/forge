# `test_when_llm_condenser_called_with_history_longer_than_keep_recent_then_older_turns_replaced_by_summary`

Pins the compaction behavior of `LlmCondenser`: when the message
history is longer than `keep_recent + 1` (the system message plus
the keep-recent window), older turns are replaced by a single
summary message produced by the injected `summarise` callable.

Per [ADR 0001](../../../../docs/adr/0001-condenser-uses-same-model-as-bench.md),
the wiring layer (cycle 19) supplies a vLLM-backed `summarise` that
calls the same model as the bench target. This unit test injects a
deterministic stub so the adapter's compaction logic is testable
without a live model.

- **Arrange**: import `LlmCondenser`, `CondenserConfig`. Build a
  7-message history (1 system + 6 turns). Build a stub
  `summarise` that returns `'STUB-SUMMARY of N=K turns'`. Construct
  `CondenserConfig(trigger_tokens=0, keep_recent=2,
  model_id='qwen3.6-27b-awq')`.
- **Act**: `condenser = LlmCondenser(summarise=stub,
  model_id='qwen3.6-27b-awq')`;
  `result = condenser.condense(messages, config)`.
- **Assert**:
  - `len(result) == 1 + 1 + 2` (system + summary + 2 recent).
  - `result[0]` equals the original system message (untouched).
  - `result[1]['role'] == 'system'` and contains the stub summary.
  - `result[-2:] == messages[-2:]` (the keep_recent window
    preserved verbatim).
  - The stub was called with a tuple of length 4 (the 4 older turns
    between system and keep_recent).

Test code: [`tests/reward_bench/adapters/test_llm_condenser.py`](../../../../tests/reward_bench/adapters/test_llm_condenser.py).
