"""Live smoke tests against the actual benched models.

These tests hit a running vLLM container and assert that the model
produces bench-relevant output. Slow (each test is one HTTP round-trip
through a real LLM); only run when the relevant container is up.
"""
import json
import os
import urllib.request

import pytest


MODELS = [
    # name, base_url
    ('qwen3.6-27b-awq', 'http://172.18.0.3:8000'),  # 5090 playground (current bench target)
    ('qwen2.5-0.5b',    'http://172.18.0.5:8000'),  # Blackwell fixture-capture (fast intermediate)
]


def _chat(base_url, api_key, model, messages, max_tokens=64, temperature=0.0):
    body = json.dumps({
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode()
    req = urllib.request.Request(
        f'{base_url}/v1/chat/completions',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    return data['choices'][0]['message']['content']


@pytest.mark.parametrize('model,base_url', MODELS, ids=lambda v: v.split('/')[-1])
def test_when_model_asked_for_a_swipe_then_reply_names_one_direction(model, base_url):
    # Arrange
    api_key = os.environ['VLLM_API_KEY']
    messages = [
        {'role': 'system',
         'content': 'You are playing 2048. The board is 4x4 with tiles. '
                    'Reply with exactly one letter for your next move: '
                    'W (up), A (left), S (down), or D (right). Nothing else.'},
        {'role': 'user',
         'content': 'Board:\n2 2 0 0\n0 0 0 0\n0 0 0 0\n0 0 0 0\nMove?'},
    ]

    # Act
    reply = _chat(base_url, api_key, model, messages)

    # Assert
    letters = {c for c in reply.upper() if c in 'WASD'}
    assert letters, f'{model} did not name a swipe direction: {reply!r}'
