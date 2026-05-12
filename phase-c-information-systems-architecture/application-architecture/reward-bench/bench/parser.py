"""Parser for tool calls emitted by the model. See spec/parser.md."""
import json
import re

_FENCE_RE = re.compile(r'```tool\b\s*(.*?)\s*```', re.DOTALL)
_TRAILING_FENCE_RE = re.compile(r'```tool\b\s*(.*)\Z', re.DOTALL)


def _parse_body(body):
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def parse_tool_calls(text):
    text = text.replace('Ġ', ' ').replace('Ċ', '\n').replace('ĉ', '\t')
    out = []
    for m in _FENCE_RE.finditer(text):
        obj = _parse_body(m.group(1))
        if obj is None:
            continue
        out.append((obj['name'], obj['args']))
    if not out:
        m = _TRAILING_FENCE_RE.search(text)
        if m:
            obj = _parse_body(m.group(1))
            if obj is not None:
                out.append((obj['name'], obj['args']))
    return out
