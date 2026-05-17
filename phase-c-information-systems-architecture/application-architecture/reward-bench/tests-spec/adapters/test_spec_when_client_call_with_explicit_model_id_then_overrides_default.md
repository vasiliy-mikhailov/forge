# `test_when_client_call_with_explicit_model_id_then_overrides_default`

Pins per-call override of `model_id`: when `call(..., model_id='X')`
is passed, the POST body's `model` field is `'X'`, not the
constructor's `default_model_id`.

## Contract

- **Arrange**: `captured: dict`; monkeypatched `urllib.request.urlopen`
  with empty-reply factory. Construct `client = VllmOpenAIClient(
  'http://stub', 'k', default_model_id='default')`.
- **Act**: `client.call([{'role': 'user', 'content': 'x'}],
  model_id='override')`.
- **Assert**: `captured['body']['model'] == 'override'`.

## Model client injection point

- **Seam**: `urllib.request.urlopen` (monkeypatched).
- **Mode**: fake.

Test code: [`../../tests/adapters/test_vllm_client_adapter.py`](../../tests/adapters/test_vllm_client_adapter.py)::`test_when_client_call_with_explicit_model_id_then_overrides_default`.

## Runtime scope

> **Runtime scope**: unit only.
