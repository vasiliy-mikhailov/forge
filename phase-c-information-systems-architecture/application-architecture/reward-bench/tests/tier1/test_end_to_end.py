"""Tier 1 end-to-end tests against live qwen3.6-27b-awq.
See src-spec/tier1/src_spec_end_to_end.md for the layered procedure.
See tests-spec/tier1/test_spec_end_to_end.md for per-test contracts."""
import json
import urllib.request


CONTAINER = 'omega-reptile-vllm-playground'


def _get_models(base_url, api_key, timeout=10):
    req = urllib.request.Request(
        f'{base_url}/v1/models',
        headers={'Authorization': f'Bearer {api_key}'},
    )
    return urllib.request.urlopen(req, timeout=timeout)


def test_when_vllm_container_serves_then_v1_models_endpoint_responds(vllm_url, vllm_api_key):
    # Arrange
    base_url = vllm_url(CONTAINER)

    # Act
    with _get_models(base_url, vllm_api_key) as r:
        status = r.status
        body = r.read()

    # Assert
    assert status == 200
    assert body, 'empty body from /v1/models'


def test_when_v1_models_queried_then_qwen3_6_27b_awq_served_name_present(vllm_url, vllm_api_key):
    # Arrange
    base_url = vllm_url(CONTAINER)

    # Act
    with _get_models(base_url, vllm_api_key) as r:
        models = json.loads(r.read())

    # Assert
    served_ids = [m['id'] for m in models['data']]
    assert 'qwen3.6-27b-awq' in served_ids, f'served={served_ids}'
