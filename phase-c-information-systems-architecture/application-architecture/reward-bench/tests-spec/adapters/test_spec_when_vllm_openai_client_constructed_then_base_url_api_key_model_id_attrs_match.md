# `test_when_vllm_openai_client_constructed_then_base_url_api_key_model_id_attrs_match`

Pins the public URL-attr surface on `VllmOpenAIClient` that the
§7 wrapper relies on per
[`../../SOLUTION-ARCHITECTURE.md`](../../SOLUTION-ARCHITECTURE.md).
The wrapper does `hasattr(model_client, 'base_url') / 'api_key' /
'model_id'` to derive legacy `vllm_*` kwargs for `run_loop`. This
test fixes the contract: the public names are `base_url`,
`api_key`, `model_id`.

- **Arrange**: `VllmOpenAIClient(base_url='http://my-vllm:8000',
  api_key='secret', default_model_id='m-42')`.
- **Act**: access `client.base_url`, `client.api_key`, `client.model_id`.
- **Assert**: each equals its constructor-supplied value.

Test code: [`../../tests/adapters/test_vllm_client_adapter.py`](../../tests/adapters/test_vllm_client_adapter.py)::`test_when_vllm_openai_client_constructed_then_base_url_api_key_model_id_attrs_match`.

## Model client injection point

- **Seam**: direct construction; no DI.
- **Mode**: pure construction, no network.

## Runtime scope

> **Runtime scope**: unit only — attribute round-trip on a freshly constructed client.
