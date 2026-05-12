"""Parser tests. See tests/specs/parser.md (cases) and spec/parser.md (contract)."""
import sys
from pathlib import Path

# Make the repo root importable so 'bench.parser' resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench.parser import parse_tool_calls


def test_when_reply_has_one_closed_tool_fence_then_returns_one_call():
    # Arrange
    reply = (
        '```tool\n'
        '{"name": "view", "args": {"path": "/a"}}\n'
        '```'
    )

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert calls == [('view', {'path': '/a'})]


def test_when_reply_has_no_tool_fence_then_returns_empty_list():
    # Arrange
    reply = 'the model said nothing useful here'

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert calls == []


def test_when_reply_has_two_closed_tool_fences_then_returns_two_calls_in_order():
    # Arrange
    reply = (
        '```tool\n'
        '{"name": "view", "args": {"path": "/a"}}\n'
        '```\n'
        '```tool\n'
        '{"name": "bash", "args": {"cmd": "ls"}}\n'
        '```'
    )

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert calls == [('view', {'path': '/a'}), ('bash', {'cmd': 'ls'})]


def test_when_reply_has_bpe_g_marker_between_json_tokens_then_detokenized_to_space():
    # Arrange — Mistral HF-quant leaks U+0120 (Ga) instead of space.
    reply = (
        '```tool\n'
        '{"name":Ġ"view", "args":Ġ{"path":Ġ"/a"}}\n'
        '```'
    )

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert calls == [('view', {'path': '/a'})]


def test_when_reply_has_bpe_c_newline_marker_then_detokenized_to_newline():
    # Arrange — U+010A leaks instead of newline.
    reply = (
        '```tool\nĊ'
        '{"name": "view", "args": {"path": "/a"}}Ċ'
        '```'
    )

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert calls == [('view', {'path': '/a'})]
