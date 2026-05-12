"""Tier 1 end-to-end tests against live qwen3.6-27b-awq.
See src-spec/tier1/code_spec_end_to_end.md for the layered procedure.
See tests-spec/tier1/test_spec_end_to_end.md for per-test Arrange/Act/Assert contracts."""
import urllib.request


CONTAINER = 'omega-reptile-vllm-playground'


def test_when_vllm_container_serves_then_v1_models_endpoint_responds(vllm_url, vllm_api_key):
    # Arrange
    base_url = vllm_url(CONTAINER)
    req = urllib.request.Request(
        f'{base_url}/v1/models',
        headers={'Authorization': f'Bearer {vllm_api_key}'},
    )

    # Act
    with urllib.request.urlopen(req, timeout=10) as r:
        status = r.status
        body = r.read()

    # Assert
    assert status == 200
    assert body, 'empty body from /v1/models'
