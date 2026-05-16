# `test_when_llm_condenser_called_with_short_messages_then_pass_through_regardless_of_count`

Pins that `LlmCondenser` is **token-aware**: it must NOT compact
just because message count exceeds `keep_recent + 1`. Compaction
only fires when the cumulative input token estimate exceeds
`config.trigger_tokens`. Cycle 18+20 made compaction
message-count-aware only, which over-fires on short turns and
inflated cycle-12 wall time 10× (56 s -> 561 s).

Token estimation: `sum(len(message['content']) // 4)` — a
4-chars-per-token heuristic. Cheap, no tokenizer dependency, good
enough to gate the condenser. The exact-token contract is
honoured by vLLMs side, not by this adapter.

- **Arrange**: import `LlmCondenser`, `CondenserConfig`. Build a
  20-message history of SHORT turns (total content ≈ 40 chars ≈
  10 tokens). `CondenserConfig(trigger_tokens=1000, keep_recent=2,
  model_id='qwen3.6-27b-awq')` — generous trigger relative to the
  test history.
- **Act**: `condenser.condense(messages, config)`.
- **Assert**:
  - `result == messages` — pass-through, no compaction.
  - `summarise` was NOT called.

The companion compaction test
([`test_spec_when_llm_condenser_compacts_then_summary_appended_to_system_message_and_older_turns_dropped`](test_spec_when_llm_condenser_compacts_then_summary_appended_to_system_message_and_older_turns_dropped.md))
already uses a generous trigger by setting `trigger_tokens=0` so
compaction is forced; that test is still valid.

Test code: [`tests/reward_bench/adapters/test_llm_condenser.py`](../../../../tests/reward_bench/adapters/test_llm_condenser.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — compaction logic over scripted summaries; live model coverage is via run_loop @live tests.

