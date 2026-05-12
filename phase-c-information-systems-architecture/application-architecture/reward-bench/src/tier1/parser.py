"""Tier 1 reply parsing. See src-spec/tier1/src_spec_when_reply_*.md."""
import re


_FENCED_PYTHON_RE = re.compile(
    r'```(?:python)?\s*\n(.*?)\n```', re.DOTALL
)


def has_fenced_python_block(reply):
    return bool(_FENCED_PYTHON_RE.search(reply))


def extract_python(reply):
    m = _FENCED_PYTHON_RE.search(reply)
    if m is None:
        raise ValueError('no fenced python block in reply')
    return m.group(1)
