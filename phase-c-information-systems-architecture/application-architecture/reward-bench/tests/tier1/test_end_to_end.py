"""Tier 1 end-to-end tests against live qwen3.6-27b-awq.
See spec/tier1/end_to_end.md for the layered procedure."""
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


def test_when_v1_models_queried_then_qwen3_6_27b_awq_served_name_present(vllm_url, vllm_api_key):
    import json
    # Arrange
    base_url = vllm_url(CONTAINER)
    req = urllib.request.Request(
        f'{base_url}/v1/models',
        headers={'Authorization': f'Bearer {vllm_api_key}'},
    )

    # Act
    with urllib.request.urlopen(req, timeout=10) as r:
        models = json.loads(r.read())

    # Assert
    served_ids = [m['id'] for m in models['data']]
    assert 'qwen3.6-27b-awq' in served_ids, f'served={served_ids}'


def test_when_chat_completion_sent_to_qwen_then_response_has_non_empty_content(vllm_url, vllm_api_key):
    import json
    # Arrange
    base_url = vllm_url(CONTAINER)
    body = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [{'role': 'user', 'content': 'Say hi.'}],
        'max_tokens': 16,
        'temperature': 0.0,
    }).encode()
    req = urllib.request.Request(
        f'{base_url}/v1/chat/completions',
        data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {vllm_api_key}'},
    )

    # Act
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())

    # Assert
    content = data['choices'][0]['message']['content']
    assert content, 'empty content'
