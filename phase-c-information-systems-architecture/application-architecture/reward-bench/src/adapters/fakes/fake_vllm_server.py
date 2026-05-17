"""FakeVllmServer adapter.

In-process responder to the two vLLM HTTP paths the bench uses:
  - `GET /v1/models`            -> served_name + max_model_len catalog
  - `POST /v1/chat/completions` -> scripted assistant reply

Installed via the conftest autouse fixture as a `urllib.request.urlopen`
replacement. Live tests opt out via `@pytest.mark.live`.
"""
from __future__ import annotations

import json
from io import BytesIO
from typing import Iterable


class _FakeResponse:
    """Quacks like the object urllib.request.urlopen returns: supports
    `.read()`, `.status`, and the context-manager protocol."""

    def __init__(self, body: bytes, status: int = 200):
        self._buf = BytesIO(body)
        self.status = status

    def read(self) -> bytes:
        return self._buf.read()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self._buf.close()


class FakeVllmServer:
    """Scripted /v1/models + /v1/chat/completions responder."""

    def __init__(
        self,
        served_name: str = 'qwen3.6-27b-awq',
        max_model_len: int = 131072,
        chat_replies: Iterable[dict] | None = None,
        default_reply: dict | None = None,
    ):
        self.served_name = served_name
        self.max_model_len = max_model_len
        self._replies = iter(chat_replies or [])
        self._default_reply = default_reply or {
            'content': '',
            'tool_calls': [],
            'role': 'assistant',
        }
        self.calls: list[dict] = []   # observability — what the test sent

    def urlopen(self, req, timeout: float = 600):
        """Mock for urllib.request.urlopen."""
        # urllib.request.Request: full_url is the resolved URL.
        url = getattr(req, 'full_url', None) or str(req)
        body = None
        if hasattr(req, 'data') and req.data:
            try:
                body = json.loads(req.data)
            except (ValueError, TypeError):
                body = None
        self.calls.append({'url': url, 'body': body})

        if url.endswith('/v1/models'):
            return _FakeResponse(json.dumps({
                'data': [{
                    'id': self.served_name,
                    'object': 'model',
                    'max_model_len': self.max_model_len,
                }],
            }).encode())

        if url.endswith('/v1/chat/completions'):
            reply = next(self._replies, self._default_reply)
            return _FakeResponse(json.dumps({
                'id': 'chatcmpl-fake',
                'object': 'chat.completion',
                'choices': [{
                    'index': 0,
                    'message': {
                        'role': reply.get('role', 'assistant'),
                        'content': reply.get('content', ''),
                        'tool_calls': reply.get('tool_calls', []),
                    },
                    'finish_reason': 'stop',
                }],
                'usage': {'prompt_tokens': 0,
                           'completion_tokens': 0,
                           'total_tokens': 0},
            }).encode())

        # Unknown path: 404-ish.
        return _FakeResponse(json.dumps({'error': f'unhandled url {url}'}).encode(),
                             status=404)
