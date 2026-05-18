"""Cycle 98b / ADR 0011: contract tests for VllmOpenAIClient adapter.

These tests stub urllib.request.urlopen so they run offline.
"""
from __future__ import annotations

import json

from src.adapters.vllm_openai_client import VllmOpenAIClient


class _FakeResp:
    def __init__(self, body: bytes): self._body = body
    def read(self) -> bytes: return self._body
    def __enter__(self): return self
    def __exit__(self, *a): pass


def _fake_urlopen_factory(captured: dict, reply_body: dict):
    def fake(req, timeout=600):
        captured['url'] = req.full_url
        captured['headers'] = dict(req.headers)
        captured['body'] = json.loads(req.data.decode())
        return _FakeResp(json.dumps(reply_body).encode())
    return fake


def test_when_client_call_invoked_then_post_to_chat_completions(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        'urllib.request.urlopen',
        _fake_urlopen_factory(captured, {
            'choices': [{'message': {'content': 'hi', 'tool_calls': []}}],
        }),
    )

    client = VllmOpenAIClient(
        base_url='http://stub:8000', api_key='k',
        default_model_id='qwen3.6-27b-awq',
    )
    reply = client.call([{'role': 'user', 'content': 'x'}])

    assert captured['url'] == 'http://stub:8000/v1/chat/completions'
    assert captured['headers']['Authorization'] == 'Bearer k'
    assert captured['body']['model'] == 'qwen3.6-27b-awq'
    assert captured['body']['messages'] == [{'role': 'user', 'content': 'x'}]
    assert reply == {'content': 'hi', 'tool_calls': []}


def test_when_client_call_given_tools_then_advertises_them(monkeypatch):
    """Cycle 96 promise lives in the adapter now."""
    captured: dict = {}
    monkeypatch.setattr(
        'urllib.request.urlopen',
        _fake_urlopen_factory(captured, {
            'choices': [{'message': {'content': '', 'tool_calls': []}}],
        }),
    )
    client = VllmOpenAIClient('http://stub', 'k')

    tools = [{'type': 'function', 'function': {'name': 'view'}}]
    client.call([{'role': 'user', 'content': 'x'}], tools=tools)

    assert captured['body']['tools'] == tools


def test_when_client_call_given_no_tools_then_field_omitted(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        'urllib.request.urlopen',
        _fake_urlopen_factory(captured, {
            'choices': [{'message': {'content': 'ok', 'tool_calls': []}}],
        }),
    )
    client = VllmOpenAIClient('http://stub', 'k')

    client.call([{'role': 'user', 'content': 'x'}])

    assert 'tools' not in captured['body'], \
        f'tools should be absent when not passed; body keys: {list(captured["body"])}'


def test_when_client_call_with_explicit_model_id_then_overrides_default(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        'urllib.request.urlopen',
        _fake_urlopen_factory(captured, {
            'choices': [{'message': {'content': '', 'tool_calls': []}}],
        }),
    )
    client = VllmOpenAIClient('http://stub', 'k', default_model_id='default')

    client.call([{'role': 'user', 'content': 'x'}], model_id='override')

    assert captured['body']['model'] == 'override'


def test_when_response_has_tool_calls_then_returned_in_reply(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        'urllib.request.urlopen',
        _fake_urlopen_factory(captured, {
            'choices': [{'message': {
                'content': '',
                'tool_calls': [{'type': 'function',
                                'function': {'name': 'view',
                                             'arguments': '{}'}}],
            }}],
        }),
    )
    client = VllmOpenAIClient('http://stub', 'k')

    reply = client.call([{'role': 'user', 'content': 'x'}])

    assert len(reply['tool_calls']) == 1
    assert reply['tool_calls'][0]['function']['name'] == 'view'


def test_when_response_message_content_is_none_then_normalized_to_empty(monkeypatch):
    """Mistral with structured tool_calls often returns content=None."""
    captured: dict = {}
    monkeypatch.setattr(
        'urllib.request.urlopen',
        _fake_urlopen_factory(captured, {
            'choices': [{'message': {'content': None, 'tool_calls': []}}],
        }),
    )
    client = VllmOpenAIClient('http://stub', 'k')

    reply = client.call([{'role': 'user', 'content': 'x'}])

    assert reply['content'] == '', f'expected "" got {reply["content"]!r}'


def test_when_vllm_openai_client_constructed_then_base_url_api_key_model_id_attrs_match():
    """Pins the public URL-attr surface on VllmOpenAIClient that the
    §7 ralph wrapper uses via hasattr."""
    # Arrange
    from src.adapters.vllm_openai_client import VllmOpenAIClient

    # Act
    client = VllmOpenAIClient(
        base_url='http://my-vllm:8000',
        api_key='secret',
        default_model_id='m-42',
    )

    # Assert
    assert client.base_url == 'http://my-vllm:8000'
    assert client.api_key == 'secret'
    assert client.model_id == 'm-42'
