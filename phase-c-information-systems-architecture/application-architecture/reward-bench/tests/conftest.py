"""Shared pytest fixtures. See src-spec/tier1/.

Cycle 99a / ADR 0014: `model_client` is a real fixture that tests
depend on. Default binding is `FakeModelClient` (offline, fast).
Tests marked `@pytest.mark.live` get the real `VllmOpenAIClient`
bound to the lab vLLM container instead — same test code, different
injected dependency.

There is NO env-variable flag. The dependency travels through the
fixture graph; that IS the DI seam.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

# Make the repo root importable so src.tier1.* resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


# Canonical happy-path script: one execute_submission with a W-only
# Solver, then finish. Tests that need different scripts construct
# their own FakeModelClient via the `fake_model_client_factory` fixture.
_DEFAULT_SOLVER_BODY = (
    "from transitions import Machine\n"
    "class Solver:\n"
    "    def __init__(self):\n"
    "        self._m = Machine(states=['idle'], initial='idle')\n"
    "    def move(self, board):\n"
    "        return 'W'\n"
)
_DEFAULT_EXEC_REPLY = (
    "```tool\n"
    '{"name": "execute_submission", "args": {}}\n'
    "===FILE_BODY===\n"
    f"{_DEFAULT_SOLVER_BODY}\n"
    "```"
)
_DEFAULT_FINISH_REPLY = (
    '```tool\n{"name": "finish", "args": {"note": "done"}}\n```'
)
_DEFAULT_SCRIPT = (
    {'content': _DEFAULT_EXEC_REPLY, 'tool_calls': []},
    {'content': _DEFAULT_FINISH_REPLY, 'tool_calls': []},
)


# Synthetic observation a happy-path execute_submission would emit.
_FAKE_EXEC_OBSERVATION = (
    '<observation>{"protocol_violations": [], '
    '"per_seed": [{"seed": 1, "score": 1000, "max_tile": 32}], '
    '"mean": 1000.0, "max_tile_best": 32, '
    '"walltime_sec_total": 0.0}</observation>'
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def fake_model_client_factory():
    """Returns a factory `(script=None) -> FakeModelClient` so tests
    can build a fake with a custom script."""
    from src.adapters.fakes.fake_model_client import FakeModelClient
    def factory(script=None):
        return FakeModelClient(script=script or _DEFAULT_SCRIPT)
    return factory


@pytest.fixture
def model_client(request, fake_model_client_factory):
    """The default-bound ModelClient under test.

    - When the test has `@pytest.mark.live`: returns a real
      `VllmOpenAIClient` constructed against the lab vLLM container.
    - Otherwise: returns a `FakeModelClient` with the canonical
      happy-path script.

    Either way, the test depends on this fixture by name. That is
    the DI seam ADR 0014 demands.
    """
    if request.node.get_closest_marker('live') is not None:
        from src.adapters.vllm_openai_client import VllmOpenAIClient
        from src.tier1.inference import ensure_serving
        return VllmOpenAIClient(
            base_url=ensure_serving(),
            api_key=os.environ['VLLM_API_KEY'],
        )
    return fake_model_client_factory()


@pytest.fixture(autouse=True)
def _bind_model_client(request, monkeypatch, model_client):
    """Autouse glue: wire the injected `model_client` into the seams
    pre-cycle-99 code still touches (`_call_model`, `ensure_serving*`,
    `execute_tool`). Cycle 99 will let run_loop take the port
    directly, removing the need for this glue.

    Live-marked tests skip the wiring so they hit the real seams.
    """
    if request.node.get_closest_marker('live') is not None:
        # Live mode: don't intercept; the test hits real vLLM.
        yield
        return

    from src.tier1 import agent_loop as al

    def fake_call_model(vllm_base_url, vllm_api_key, messages,
                        max_tokens=12288, temperature=0.0,
                        model_id='qwen3.6-27b-awq'):
        return model_client.call(
            messages,
            tools=list(al.TOOL_SCHEMAS),
            temperature=temperature,
            max_tokens=max_tokens,
            model_id=model_id,
        )
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    def fake_execute_tool(name, args, workspace, env_dir, tasks_dir,
                          dev_hard_wall_sec=None, **_):
        if name == 'execute_submission':
            try:
                (workspace / 'submission.py').write_text(
                    args.get('content', ''))
            except Exception:
                pass
            return _FAKE_EXEC_OBSERVATION
        if name == 'finish':
            return f'<finish>{args.get("note", "")}</finish>'
        if name == 'view':
            return '<view>(faked)</view>'
        return f'<error>unknown tool: {name}</error>'
    monkeypatch.setattr(al, 'execute_tool', fake_execute_tool)

    # Make sure tests that import inference.ensure_serving_model get
    # a non-routable URL (and never block).
    from src.tier1 import inference as inf
    monkeypatch.setattr(inf, 'ensure_serving',
                        lambda: 'http://fake:8000')
    monkeypatch.setattr(inf, 'ensure_serving_model',
                        lambda target: 'http://fake:8000')
    monkeypatch.setenv('VLLM_API_KEY', 'fake-key')

    yield


# ============================================================
# Live-only fixtures (only used by @pytest.mark.live tests)
# ============================================================

@pytest.fixture(scope='session')
def vllm_api_key():
    return os.environ['VLLM_API_KEY']


@pytest.fixture(scope='session')
def vllm_base_url():
    from src.tier1.inference import ensure_serving
    return ensure_serving()


@pytest.fixture(scope='session')
def skill_tier1_reply(vllm_base_url, vllm_api_key):
    """Live-only: cached one-shot reply for tests that grep the model's
    fenced-python output."""
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


@pytest.fixture(scope='session')
def tool_protocol_reply(vllm_base_url, vllm_api_key):
    """Live-only: cached one-shot reply under the interactive protocol."""
    from src.tier1.agent_loop import SYSTEM_PROMPT, FIRST_USER
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': FIRST_USER},
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
