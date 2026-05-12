"""Shared pytest fixtures. See src-spec/tier1/."""
import json
import os
import sys
import urllib.request
from pathlib import Path

# Make the repo root importable so src.tier1.* resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


@pytest.fixture(scope='session')
def vllm_api_key():
    return os.environ['VLLM_API_KEY']


@pytest.fixture(scope='session')
def vllm_base_url():
    """Base URL of the lab vLLM container, brought up by the bench itself."""
    from src.tier1.inference import ensure_serving
    return ensure_serving()


@pytest.fixture(scope='session')
def skill_tier1_reply(vllm_base_url, vllm_api_key):
    """Live model reply to the SKILL_tier1.md prompt. One call per pytest session,
    shared across all downstream tests that consume the reply."""
    repo = Path(__file__).resolve().parent.parent
    skill = (repo / 'tasks/2048/SKILL_tier1.md').read_text()
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [
            {'role': 'system',
             'content': 'You are a reward-bench Tier 1 author. Read the task spec and respond with the final Python module inside a single fenced python code block. No prose outside the fence.'},
            {'role': 'user', 'content': skill},
        ],
        'max_tokens': 32768,
        'temperature': 0.0,
    }).encode()
    req = urllib.request.Request(
        f'{vllm_base_url}/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {vllm_api_key}',
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read())
    return data['choices'][0]['message']['content']
