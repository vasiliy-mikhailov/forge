"""Shared pytest fixtures. See src-spec/tier1/."""
import os
import sys
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
