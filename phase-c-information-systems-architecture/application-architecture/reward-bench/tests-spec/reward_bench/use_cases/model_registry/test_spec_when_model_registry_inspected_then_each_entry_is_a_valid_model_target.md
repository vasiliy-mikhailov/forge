# `test_when_model_registry_inspected_then_each_entry_is_a_valid_model_target`
Pins the contract of `MODEL_REGISTRY`: every entry is a valid
`ModelTarget`, no field is empty, the registry has exactly 21
entries, and all `id`s are unique.
- **Arrange**: import `MODEL_REGISTRY` from
 `src.reward_bench.use_cases.model_registry`.
- **Act**: inspect each entry's fields and the tuple's overall shape.
- **Assert**:
 - `len(MODEL_REGISTRY) == 21` (the count anchors against silent
 drops; if a model is removed the test fails loudly).
 - For every `target` in the tuple, every field
 (`id`, `hf_path`, `served_name`, `tool_call_parser`) is a
 non-empty string AND `max_model_len` is a positive int.
 - Across the tuple, every `id` is unique (registry-key invariant).
 - Every `tool_call_parser` is in the allowed parser set
 `{qwen3_xml, mistral, gemma4, llama3_json, hermes, openai}`.
This is the bench's coverage probe across the leaderboard. Adding
a new model to `MODEL_REGISTRY` automatically adds a test case;
drift between `models.yml` and the Python registry surfaces as a
failure on the next pytest run.
Test code: [`tests/reward_bench/use_cases/test_model_registry.py`](../../../../tests/reward_bench/use_cases/test_model_registry.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — MODEL_REGISTRY tuple contract; pure-Python data; scale-invariant.
