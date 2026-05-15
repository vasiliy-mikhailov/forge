"""Cycle 98 / ADR 0011: FencedTextParser adapter.

Reads cycle-9/58 fenced ```tool blocks out of AssistantReply.content:

    ```tool
    {"name": "execute_submission", "args": {}}
    ===FILE_BODY===
    ...raw python...
    ```

Lifted verbatim from the pre-cycle-98 `parse_tool_calls` body in
src/tier1/agent_loop.py (cycles 9, 51, 58). Defensive: bad JSON in one
block does not abort the iter — the block is skipped (cycle 51
hypothesis #9).
"""
from __future__ import annotations

import json
import re

from src.ports.protocol_parser import AssistantReply, ProtocolParser, ToolCall


_TOOL_BLOCK_RE = re.compile(r'```tool\b\s*\n(.*?)\n```', re.DOTALL)
_BODY_SPLIT_RE = re.compile(r'\n===FILE_BODY===\s*\n', re.DOTALL)


class FencedTextParser(ProtocolParser):
    """Extracts tool calls from ```tool fenced blocks in content."""

    def extract(self, reply: AssistantReply) -> list[ToolCall]:
        content = reply.get('content') or ''
        out: list[ToolCall] = []
        for m in _TOOL_BLOCK_RE.finditer(content):
            raw = m.group(1)
            parts = _BODY_SPLIT_RE.split(raw, maxsplit=1)
            json_part = parts[0].strip()
            body_part = parts[1] if len(parts) == 2 else None
            try:
                obj = json.loads(json_part)
            except json.JSONDecodeError:
                # Cycle 51 fallback: strip trailing commas/whitespace
                # and retry once.
                try:
                    obj = json.loads(json_part.rstrip(', \t\n'))
                except json.JSONDecodeError:
                    continue
            if not isinstance(obj, dict):
                continue
            name = str(obj.get('name', '')).strip()
            if not name:
                continue
            raw_args = obj.get('args') or {}
            if not isinstance(raw_args, dict):
                raw_args = {}
            args = dict(raw_args)
            if body_part is not None:
                args['content'] = body_part
            out.append(ToolCall(name=name, args=args))
        return out
