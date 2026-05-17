# `test_when_client_call_invoked_then_post_to_chat_completions`

Pins the basic POST contract of `VllmOpenAIClient.call`: hits
`{base_url}/v1/chat/completions`, threads `Authorization: Bearer
{api_key}`, sends body with `model`, `messages`, returns the
assistant reply normalised to `{'content': str, 'tool_calls': list}`.

## Contract

- **Arrange**: `captured: dict`. Monkeypatch `urllib.request.urlopen`
  with `_fake_urlopen_factory(captured, {'choices': [{'message':
  {'content': 'hi', 'tool_calls': []}}]})`. Construct
  `client = VllmOpenAIClient(base_url='http://stub:8000', api_key='k',
  default_model_id='qwen3.6-27b-awq')`.
- **Act**: `reply = client.call([{'role': 'user', 'content': 'x'}])`.
- **Assert**: `captured['url'] == 'http://stub:8000/v1/chat/completions'`;
  `captured['headers']['Authorization'] == 'Bearer k'`;
  `captured['body']['model'] == 'qwen3.6-27b-awq'`;
  `captured['body']['messages'] == [{'role':'user','content':'x'}]`;
  `reply == {'content': 'hi', 'tool_calls': []}`.

## Model client injection point

- **Seam**: `urllib.request.urlopen` (monkeypatched).
- **Mode**: fake.

Test code: [`../../tests/adapters/test_vllm_client_adapter.py`](../../tests/adapters/test_vllm_client_adapter.py)::`test_when_client_call_invoked_then_post_to_chat_completions`.

## Runtime scope

> **Runtime scope**: unit only.
