# `test_when_client_call_given_tools_then_advertises_them`

Pins that `VllmOpenAIClient.call(messages, tools=[...])` lands the
caller's `tools` list verbatim in the POST body — so vLLM's per-model
parsers (mistral / devstral / gpt-oss) can emit structured
`message.tool_calls`. Loss of this field reverts those model families
to "I do not have the tools needed".

## Contract

- **Arrange**: a `captured: dict` recorder. Monkeypatch
  `urllib.request.urlopen` with a fake produced by
  `_fake_urlopen_factory(captured, response_payload)` where
  `response_payload = {'choices': [{'message': {'content': '',
  'tool_calls': []}}]}` (minimal valid OpenAI chat-completions reply).
  Construct `client = VllmOpenAIClient('http://stub', 'k')`.
  Define `tools = [{'type': 'function', 'function': {'name': 'view'}}]`.
- **Act**: `client.call([{'role': 'user', 'content': 'x'}], tools=tools)`.
- **Assert**: `captured['body']['tools'] == tools` — the list lands in
  the body identically (same object shape, same nested dict, same
  ordering).

## Model client injection point

- **Seam**: `urllib.request.urlopen` (monkeypatched per-test).
- **Mode**: fake — the recorder captures the request and synthesises
  the response; no network.
- **Override**: not applicable (test exercises the production
  `VllmOpenAIClient` directly).

Test code: [`../../tests/adapters/test_vllm_client_adapter.py`](../../tests/adapters/test_vllm_client_adapter.py)::`test_when_client_call_given_tools_then_advertises_them`.

## Runtime scope

> **Runtime scope**: unit only — adapter wire-format contract; the
> live-runtime test for the same boundary lives at
> [`tests/tier1/test_inference.py`](../../../tests/tier1/test_inference.py)
> (real vLLM container).
