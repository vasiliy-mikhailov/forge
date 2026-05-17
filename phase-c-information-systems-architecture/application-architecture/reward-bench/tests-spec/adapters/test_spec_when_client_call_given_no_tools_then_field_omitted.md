# `test_when_client_call_given_no_tools_then_field_omitted`

Pins that `VllmOpenAIClient.call(messages)` (no `tools` kwarg) omits
the `tools` key from the POST body entirely — not `tools: []`,
absent. Pairs with `..._given_tools_then_advertises_them`.

## Contract

- **Arrange**: `captured: dict` recorder; monkeypatch
  `urllib.request.urlopen` with `_fake_urlopen_factory(captured,
  {'choices': [{'message': {'content': 'ok', 'tool_calls': []}}]})`.
  Construct `client = VllmOpenAIClient('http://stub', 'k')`.
- **Act**: `client.call([{'role': 'user', 'content': 'x'}])` — no
  `tools` kwarg.
- **Assert**: `'tools' not in captured['body']`.

## Model client injection point

- **Seam**: `urllib.request.urlopen` (monkeypatched).
- **Mode**: fake.

Test code: [`../../tests/adapters/test_vllm_client_adapter.py`](../../tests/adapters/test_vllm_client_adapter.py)::`test_when_client_call_given_no_tools_then_field_omitted`.

## Runtime scope

> **Runtime scope**: unit only.
