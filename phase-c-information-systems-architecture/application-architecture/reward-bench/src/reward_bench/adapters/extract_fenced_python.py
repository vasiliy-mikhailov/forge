"""§4 helper — extract the last fenced python block from an agent's
final assistant message.

Per SOLUTION-ARCHITECTURE.md §4 binding interface: the agent
emits its final Solver code as a fenced ```python ... ``` (or
plain ``` ... ```) block in its last message. This helper lifts
the body out as a string. Empty string if no fence found.
"""
from __future__ import annotations

import re


_FENCE_RE = re.compile(
    r'```[ \t]*(?:python|py)?[ \t]*\n(.*?)```',
    re.DOTALL,
)


def extract_fenced_python(msg: str) -> str:
    """Return the inner text of the *last* fenced block in `msg`.

    Recognises both ```python and bare ``` fences. Returns '' if
    no block is found.
    """
    matches = _FENCE_RE.findall(msg)
    return matches[-1] if matches else ''
