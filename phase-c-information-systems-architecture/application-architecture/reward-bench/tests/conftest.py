"""Shared pytest fixtures."""
import os
import subprocess

import pytest


@pytest.fixture(scope='session')
def vllm_url():
    """Resolve a vLLM container's URL by docker inspect at test time."""
    def _resolve(container_name):
        out = subprocess.run(
            ['docker', 'inspect', container_name,
             '--format', '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}'],
            capture_output=True, text=True, check=True,
        )
        ip = out.stdout.strip()
        if not ip:
            pytest.skip(f'container {container_name} not on proxy-net')
        return f'http://{ip}:8000'
    return _resolve


@pytest.fixture(scope='session')
def vllm_api_key():
    return os.environ['VLLM_API_KEY']
