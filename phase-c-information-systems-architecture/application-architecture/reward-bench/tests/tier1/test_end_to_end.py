"""Tier 1 end-to-end tests against live qwen3.6-27b-awq.
See src-spec/tier1/ (per-behavior src_spec_when_*.md files) for the layered procedure.
See tests-spec/tier1/ (per-behavior test_spec_when_*.md files) for per-test contracts."""
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


def test_when_chat_completion_sent_then_response_has_non_empty_content(vllm_url, vllm_api_key):
    # Arrange
    base_url = vllm_url(CONTAINER)
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [{'role': 'user', 'content': 'Say hi.'}],
        'max_tokens': 16,
        'temperature': 0.0,
    }).encode()
    req = urllib.request.Request(
        f'{base_url}/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {vllm_api_key}',
        },
    )

    # Act
    with urllib.request.urlopen(req, timeout=60) as r:
        status = r.status
        data = json.loads(r.read())

    # Assert
    assert status == 200
    content = data['choices'][0]['message']['content']
    assert content, 'empty content'


def test_when_skill_tier1_prompt_sent_then_reply_completes_within_5_min(vllm_url, vllm_api_key):
    from pathlib import Path
    # Arrange
    base_url = vllm_url(CONTAINER)
    repo = Path(__file__).resolve().parents[2]
    skill = (repo / 'tasks/2048/SKILL_tier1.md').read_text()
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [
            {'role': 'system', 'content': 'You are a reward-bench Tier 1 author. Read the task spec and respond with the final Python module inside a single fenced python code block. No prose outside the fence.'},
            {'role': 'user', 'content': skill},
        ],
        'max_tokens': 32768,
        'temperature': 0.0,
    }).encode()
    req = urllib.request.Request(
        f'{base_url}/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {vllm_api_key}',
        },
    )

    # Act
    with urllib.request.urlopen(req, timeout=300) as r:
        status = r.status
        data = json.loads(r.read())

    # Assert
    assert status == 200
    content = data['choices'][0]['message']['content']
    assert content, 'empty content'
