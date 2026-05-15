"""Cycle 99 proper / ADR 0011 step 2: run_loop port-DI tests."""
from __future__ import annotations

import pytest


@pytest.mark.no_fake
def test_when_run_loop_called_with_model_client_then_calls_pass_through_port(tmp_path):
    """Cycle 99: passing model_client=X to run_loop means X.call() is
    used instead of the module-level _call_model. No monkeypatching."""
    from src.adapters.fakes.fake_model_client import FakeModelClient
    from src.tier1.agent_loop import run_loop

    script = (
        {
            'content': '```tool\n{"name": "finish", "args": {"note": "ok"}}\n```',
            'tool_calls': [],
        },
    )
    fake = FakeModelClient(script=script)

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    result = run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://unused', vllm_api_key='unused',
        max_iters=3,
        model_client=fake,   # cycle 99: explicit injection
    )

    # The fake was called at least once.
    assert len(fake.calls) >= 1, f'fake not exercised; calls={fake.calls}'
    # The loop completed via the scripted `finish` reply.
    assert result['finished'] is True
    # No tools were advertised by default — the legacy TOOL_SCHEMAS is
    # still the fallback when no tool_registry is also passed.
    assert fake.calls[0]['tools'] is not None
    assert len(fake.calls[0]['tools']) == 3


@pytest.mark.no_fake
def test_when_run_loop_called_with_tool_registry_then_dispatch_goes_through_port(tmp_path):
    """Cycle 99: passing tool_registry=R means R.dispatch() handles
    tool calls instead of the module-level execute_tool."""
    from src.adapters.fakes.fake_model_client import FakeModelClient
    from src.ports.tool_registry import ToolRegistry
    from src.tier1.agent_loop import run_loop

    class RecordingRegistry(ToolRegistry):
        """Test registry: schemas mirror prod; dispatch records calls."""

        def __init__(self):
            from src.adapters.tier1_tool_registry import Tier1ToolRegistry
            self._real = Tier1ToolRegistry()
            self.dispatched: list[tuple[str, dict]] = []

        @property
        def schemas(self):
            return self._real.schemas

        def dispatch(self, name, args, ctx):
            self.dispatched.append((name, args))
            if name == 'finish':
                return '<finish>ok</finish>'
            return '<ok>(faked dispatch)</ok>'

    registry = RecordingRegistry()
    fake_client = FakeModelClient(script=(
        {'content': '```tool\n{"name": "finish", "args": {"note": "z"}}\n```',
         'tool_calls': []},
    ))

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    result = run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://unused', vllm_api_key='unused',
        max_iters=3,
        model_client=fake_client,
        tool_registry=registry,
    )

    assert result['finished'] is True
    assert registry.dispatched == [('finish', {'note': 'z'})], (
        f'dispatch records: {registry.dispatched}'
    )


@pytest.mark.no_fake
def test_when_run_loop_called_with_protocol_parser_then_extract_goes_through_port(tmp_path):
    """Cycle 99: passing protocol_parser=P means P.extract() decodes
    replies instead of the module-level parse_tool_calls."""
    from src.adapters.fakes.fake_model_client import FakeModelClient
    from src.ports.protocol_parser import ProtocolParser, ToolCall
    from src.tier1.agent_loop import run_loop

    class RecordingParser(ProtocolParser):
        def __init__(self):
            self.calls: list = []

        def extract(self, reply):
            self.calls.append(reply)
            # Always return a single 'finish' call to terminate quickly.
            return [ToolCall(name='finish', args={'note': 'parsed'})]

    parser = RecordingParser()
    fake_client = FakeModelClient(script=(
        {'content': 'whatever — the parser ignores content', 'tool_calls': []},
    ))

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    result = run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://unused', vllm_api_key='unused',
        max_iters=3,
        model_client=fake_client,
        protocol_parser=parser,
    )

    assert result['finished'] is True
    # The parser was invoked at least once; with the scripted finish
    # reply, the loop terminates on iter 1.
    assert len(parser.calls) >= 1


@pytest.mark.no_fake
def test_when_run_loop_called_without_ports_then_legacy_seams_used(tmp_path, monkeypatch):
    """Cycle 99 back-compat: pre-cycle-99 callers (no ports passed)
    still go through the module-level _call_model / execute_tool /
    parse_tool_calls so existing monkeypatching tests stay green."""
    from src.tier1 import agent_loop as al

    fake_call_count = {'n': 0}

    def fake_call_model(vllm_base_url, vllm_api_key, messages,
                        max_tokens=12288, temperature=0.0,
                        model_id='qwen3.6-27b-awq'):
        fake_call_count['n'] += 1
        return {
            'content': '```tool\n{"name": "finish", "args": {"note": "legacy"}}\n```',
            'tool_calls': [],
        }
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub', max_iters=3,
        # NO model_client / tool_registry / protocol_parser — falls back
        # to legacy module-level seams.
    )

    assert result['finished'] is True
    assert fake_call_count['n'] >= 1, (
        'legacy _call_model seam should have been invoked when no '
        f'model_client was passed; count={fake_call_count["n"]}'
    )
