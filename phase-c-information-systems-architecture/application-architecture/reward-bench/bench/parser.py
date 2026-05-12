"""Parser for tool calls emitted by the model. See spec/parser.md."""
import json
import re

_FENCE_RE = re.compile(r'```tool\b\s*(.*?)\s*```', re.DOTALL)
_TRAILING_FENCE_RE = re.compile(r'```tool\b\s*(.*)\Z', re.DOTALL)


def parse_tool_calls(text):
    text = text.replace('Ġ', ' ').replace('Ċ', '\n').replace('ĉ', '\t')
    out = []
    for m in _FENCE_RE.finditer(text):
        obj = json.loads(m.group(1))
        out.append((obj['name'], obj['args']))
    if not out:
        m = _TRAILING_FENCE_RE.search(text)
        if m:
            obj = json.loads(m.group(1))
            out.append((obj['name'], obj['args']))
    return out
