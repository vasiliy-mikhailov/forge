# `test_when_response_has_tool_calls_then_returned_in_reply`

Pins that structured `tool_calls` in the OpenAI response pass through
the adapter unchanged into the returned reply, available to the
`StructuredOpenAIParser` downstream.

## Contract

- **Arrange**: monkeypatched `urllib.request.urlopen` returning
  `{'choices': [{'message': {'content': '', 'tool_calls':
  [{'type':'function','function':{'name':'view','arguments':'{}'}}]}}]}`.
  Construct `client = VllmOpenAIClient('http://stub', 'k')`.
- **Act**: `reply = client.call([{'role':'user','content':'x'}])`.
- **Assert**: `len(reply['tool_calls']) == 1`;
  `reply['tool_calls'][0]['function']['name'] == 'view'`.

## Model client injection point

- **Seam**: `urllib.request.urlopen` (monkeypatched).
- **Mode**: fake.

Test code: [`../../tests/adapters/test_vllm_client_adapter.py`](../../tests/adapters/test_vllm_client_adapter.py)::`test_when_response_has_tool_calls_then_returned_in_reply`.

## Runtime scope

> **Runtime scope**: unit only.
