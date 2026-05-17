# `test_when_response_message_content_is_none_then_normalized_to_empty`

Pins the mistral-family quirk handling: when `message.content` is
`None` (mistral returns this whenever `tool_calls` is set), the
adapter normalises it to `''` so downstream parsers can call
`.strip()` / regex without a None-check.

## Contract

- **Arrange**: monkeypatched `urllib.request.urlopen` returning
  `{'choices': [{'message': {'content': None, 'tool_calls': []}}]}`.
  Construct `client = VllmOpenAIClient('http://stub', 'k')`.
- **Act**: `reply = client.call([{'role':'user','content':'x'}])`.
- **Assert**: `reply['content'] == ''`.

## Model client injection point

- **Seam**: `urllib.request.urlopen` (monkeypatched).
- **Mode**: fake.

Test code: [`../../tests/adapters/test_vllm_client_adapter.py`](../../tests/adapters/test_vllm_client_adapter.py)::`test_when_response_message_content_is_none_then_normalized_to_empty`.

## Runtime scope

> **Runtime scope**: unit only.
