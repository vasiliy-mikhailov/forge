"""StructuredOpenAIParser adapter.

Reads OpenAI tool_calls out of AssistantReply.tool_calls. Defensive:
  - malformed function.arguments JSON -> empty args
  - vLLM mistral tokenizer leaking U+0120 / U+2581 stripped before json.loads
  - function.arguments arriving as dict in non-strict vLLM modes
"""
from __future__ import annotations

import json

from src.ports.protocol_parser import AssistantReply, ProtocolParser, ToolCall


class StructuredOpenAIParser(ProtocolParser):
    """Extracts tool calls from message.tool_calls (OpenAI shape)."""

    def extract(self, reply: AssistantReply) -> list[ToolCall]:
        structured = reply.get('tool_calls') or []
        out: list[ToolCall] = []
        for tc in structured:
            if not isinstance(tc, dict):
                continue
            fn = tc.get('function') or {}
            if not isinstance(fn, dict):
                continue
            name = str(fn.get('name', '')).strip()
            if not name:
                continue
            raw_args = fn.get('arguments')
            args: dict = {}
            if isinstance(raw_args, str):
                # Strip SentencePiece artefacts (U+0120 Ġ, U+2581 ▁); no-op on well-formed JSON.
                cleaned = raw_args.replace('Ġ', ' ').replace('▁', ' ')
                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, dict):
                    args = parsed
            elif isinstance(raw_args, dict):
                # Non-strict vLLM modes emit arguments as a dict directly.
                args = dict(raw_args)
            out.append(ToolCall(name=name, args=args))
        return out
