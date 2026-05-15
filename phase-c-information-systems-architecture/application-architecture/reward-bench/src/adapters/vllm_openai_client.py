"""Cycle 98b / ADR 0011: VllmOpenAIClient adapter.

Lifted verbatim from the pre-cycle-98b `_call_model` in
src/tier1/agent_loop.py (cycles 11, 74, 83, 96). Sends an OpenAI-style
Chat-Completions request to a vLLM `/v1/chat/completions` endpoint
and returns the {content, tool_calls} shape.
"""
from __future__ import annotations

import json
import urllib.request

from src.ports.model_client import ModelClient
from src.ports.protocol_parser import AssistantReply


class VllmOpenAIClient(ModelClient):
    """vLLM `/v1/chat/completions` client. Constructed with base URL +
    API key + default model_id; per-call kwargs override."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        default_model_id: str = 'qwen3.6-27b-awq',
        timeout_sec: float = 600.0,
    ):
        self._base_url = base_url
        self._api_key = api_key
        self._default_model_id = default_model_id
        self._timeout_sec = timeout_sec

    def call(
        self,
        messages: list[dict],
        *,
        tools: list[dict] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 12288,
        model_id: str | None = None,
    ) -> AssistantReply:
        payload: dict = {
            'model': model_id or self._default_model_id,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
        }
        if tools:
            # Cycle 96: advertise tools so vLLM per-model parsers
            # (mistral / openai_oss / etc.) route structured calls.
            payload['tools'] = list(tools)
        req = urllib.request.Request(
            f'{self._base_url}/v1/chat/completions',
            data=json.dumps(payload).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self._api_key}',
            },
        )
        with urllib.request.urlopen(req, timeout=self._timeout_sec) as r:
            data = json.loads(r.read())
        msg = data['choices'][0]['message']
        return {
            'content': msg.get('content') or '',
            'tool_calls': msg.get('tool_calls') or [],
        }
