"""Live smoke tests against the currently benched model.

Pinned to qwen3.6-27b-awq on the 5090. Multi-model parameterization will
return when the test suite is large enough that runtime against a single
27B model becomes the bottleneck — not before.
"""
import json
import urllib.request


MODEL = 'qwen3.6-27b-awq'
CONTAINER = 'omega-reptile-vllm-playground'


def _chat(base_url, api_key, messages, max_tokens=64, temperature=0.0):
    body = json.dumps({
        'model': MODEL,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode()
    req = urllib.request.Request(
        f'{base_url}/v1/chat/completions',
        data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {api_key}'},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    return data['choices'][0]['message']['content']


def test_when_model_asked_for_a_swipe_then_reply_names_one_direction(vllm_url, vllm_api_key):
    # Arrange
    base_url = vllm_url(CONTAINER)
    messages = [
        {'role': 'system',
         'content': 'You are playing 2048. The board is 4x4 with tiles. '
                    'Reply with exactly one letter for your next move: '
                    'W (up), A (left), S (down), or D (right). Nothing else.'},
        {'role': 'user',
         'content': 'Board:\n2 2 0 0\n0 0 0 0\n0 0 0 0\n0 0 0 0\nMove?'},
    ]

    # Act
    reply = _chat(base_url, vllm_api_key, messages)

    # Assert
    letters = {c for c in reply.upper() if c in 'WASD'}
    assert letters, f'no swipe direction in reply: {reply!r}'


def test_when_model_asked_for_tier1_solver_then_reply_contains_class_solver_using_transitions(
        vllm_url, vllm_api_key):
    # Arrange
    base_url = vllm_url(CONTAINER)
    messages = [
        {'role': 'system',
         'content': 'You are writing a 2048 solver as a Python module per '
                    'reward-bench Tier 1. The module MUST define class Solver '
                    'with a method move(self, board: list[list[int]]) -> str '
                    'returning one of "W", "A", "S", "D". The class '
                    'MUST use the transitions library to declare its FSM. '
                    'Include an import from transitions at the top.'},
        {'role': 'user',
         'content': 'Write the full Python module. Reply with only the code, '
                    'no markdown fences, no explanation.'},
    ]

    # Act
    reply = _chat(base_url, vllm_api_key, messages, max_tokens=1500)

    # Assert
    assert 'class Solver' in reply, f'no class Solver in reply: {reply!r}'
    assert 'from transitions' in reply, f'no transitions import in reply: {reply!r}'
