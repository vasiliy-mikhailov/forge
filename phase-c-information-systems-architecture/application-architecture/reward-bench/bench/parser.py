"""Parser for tool calls emitted by the model. See spec/parser.md."""
import json
import re

_FENCE_RE = re.compile(r'```tool\b\s*(.*?)\s*```', re.DOTALL)


def parse_tool_calls(text):
    out = []
    for m in _FENCE_RE.finditer(text):
        obj = json.loads(m.group(1))
        out.append((obj['name'], obj['args']))
    return out
