# `src_spec_vllm_openai_client_speaks_chat_completions`

[`VllmOpenAIClient`](../../../src/adapters/vllm_openai_client.py) is the
production [`ModelClient`](../../../src/ports/model_client.py) binding.
Cycles 11, 74, 83, 96.

## Contract

Constructed with `(base_url, api_key, default_model_id, timeout_sec=600)`.

`call(messages, *, tools, temperature, max_tokens, model_id)`:

1. POSTs to `f"{base_url}/v1/chat/completions"` with
   `Authorization: Bearer {api_key}`, `Content-Type: application/json`.
2. JSON body: `{model, messages, max_tokens, temperature}`. When
   `tools` is non-empty, payload also includes `tools=[...]` (cycle 96
   wired this so mistral / devstral / gpt-oss emit structured
   tool_calls).
3. Reads `data['choices'][0]['message']`. Returns
   `{'content': msg.content or '', 'tool_calls': msg.tool_calls or []}`.
   Empty-string normalisation on `content=None` (mistral quirk).
