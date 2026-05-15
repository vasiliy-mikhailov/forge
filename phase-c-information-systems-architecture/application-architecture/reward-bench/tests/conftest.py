"""Shared pytest fixtures. See src-spec/tier1/.

Cycle 99a / ADR 0014: `model_client` is a real fixture that tests
depend on. Default binding is `FakeModelClient` (offline, fast).
Tests marked `@pytest.mark.live` get the real `VllmOpenAIClient`
bound to the lab vLLM container instead — same test code, different
injected dependency.

Cycle 101 / ADR 0012: a `FakeVllmServer` is also bound at the
`urllib.request.urlopen` seam so live-by-nature tests (test_inference,
skill_tier1_reply, tool_protocol_reply) run offline too. They get a
canned `/v1/models` catalog and a canned `/v1/chat/completions` reply.

There is NO env-variable flag. Dependencies travel through the
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

# Default reply for the direct-urlopen path (test_inference + the
# session-scoped reply fixtures). A fenced python block satisfies the
# `skill_tier1_reply` parser tests; the chat tool-protocol replies use
# `_DEFAULT_EXEC_REPLY` shape.
_FAKE_FENCED_PYTHON_REPLY = (
    "Here is the Solver module:\n\n"
    "```python\n"
    f"{_DEFAULT_SOLVER_BODY}\n"
    "```"
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
    """Returns a factory `(script=None) -> FakeModelClient`."""
    from src.adapters.fakes.fake_model_client import FakeModelClient
    def factory(script=None):
        return FakeModelClient(script=script or _DEFAULT_SCRIPT)
    return factory


@pytest.fixture
def fake_vllm_server_factory():
    """Returns a factory `(**kwargs) -> FakeVllmServer`. Tests that need
    custom canned replies build their own."""
    from src.adapters.fakes.fake_vllm_server import FakeVllmServer
    def factory(**kwargs):
        return FakeVllmServer(**kwargs)
    return factory


@pytest.fixture
def model_client(request, fake_model_client_factory):
    """The default-bound ModelClient under test."""
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
    """Autouse glue: wire the injected `model_client` AND a
    `FakeVllmServer` into the seams pre-cycle-99 code still touches
    (`_call_model`, `execute_tool`, `ensure_serving*`, plus
    `urllib.request.urlopen` for direct /v1/* calls).
    """
    if (request.node.get_closest_marker('live') is not None
            or request.node.get_closest_marker('no_fake') is not None):
        yield
        return

    from src.tier1 import agent_loop as al
    from src.adapters.fakes.fake_vllm_server import FakeVllmServer

    # FakeVllmServer: serves /v1/models + /v1/chat/completions.
    # Default reply is a fenced-python block (satisfies parser tests
    # AND most chat tests; tests that need a different shape can
    # construct their own server via the factory and re-monkeypatch).
    fake_server = FakeVllmServer(
        default_reply={'content': _FAKE_FENCED_PYTHON_REPLY, 'tool_calls': []},
    )
    monkeypatch.setattr(
        'urllib.request.urlopen',
        lambda req, timeout=600: fake_server.urlopen(req, timeout=timeout),
    )

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

    # ensure_serving / ensure_serving_model: return a non-routable URL
    # (the FakeVllmServer intercepts urlopen, so the URL never matters).
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
    return os.environ.get('VLLM_API_KEY', 'fake-key')


@pytest.fixture(scope='session')
def vllm_base_url():
    return 'http://fake:8000'   # autouse urlopen mock handles the real path


@pytest.fixture
def skill_tier1_reply():
    """Default-bound: returns the fenced-python fake. Live tests get
    the real model reply via the session-scoped live override below."""
    return _FAKE_FENCED_PYTHON_REPLY


@pytest.fixture
def tool_protocol_reply():
    """Default-bound: returns the fenced-tool fake."""
    return _DEFAULT_EXEC_REPLY


# Live session-scoped overrides — only consulted when a test explicitly
# requests them AND has @pytest.mark.live. The autouse fixture's
# early-yield branch bypasses the urlopen mock for live tests; these
# session fixtures then perform real urlopen.

@pytest.fixture(scope='session')
def skill_tier1_reply_live(vllm_api_key):
    """Live-only: one-shot real model reply to SKILL_tier1.md."""
    from src.tier1.inference import ensure_serving
    base_url = ensure_serving()
    repo = Path(__file__).resolve().parent.parent
    skill = (repo / 'tasks/2048/SKILL_tier1.md').read_text()
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [
            {'role': 'system',
             'content': 'You are a reward-bench Tier 1 author. Read the task spec and respond with the final Python module inside a single fenced python code block. No prose outside the fence.'},
            {'role': 'user', 'content': skill},
        ],
        'max_tokens': 4096,
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
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read())
    return data['choices'][0]['message']['content']


@pytest.fixture(scope='session')
def tool_protocol_reply_live(vllm_api_key):
    """Live-only: real model reply under the interactive protocol."""
    from src.tier1.inference import ensure_serving
    from src.tier1.agent_loop import SYSTEM_PROMPT, FIRST_USER
    base_url = ensure_serving()
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': FIRST_USER},
        ],
        'max_tokens': 4096,
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
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read())
    return data['choices'][0]['message']['content']
