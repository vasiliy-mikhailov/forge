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


def test_when_reply_has_bpe_tab_marker_then_detokenized_to_tab():
    # Arrange — U+0109 (lowercase c-circumflex) leaks instead of tab.
    reply = (
        '```tool\n'
        '{"name":ĉ"view",\t"args":\t{"path":\t"/a"}}\n'
        '```'
    )

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert calls == [('view', {'path': '/a'})]


def test_when_reply_ends_with_unclosed_tool_fence_then_returns_one_call():
    # Arrange — Qwen-3.6 hits gen cap before closing fence lands.
    reply = (
        '```tool\n'
        '{"name": "view", "args": {"path": "/a"}}'
    )

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert calls == [('view', {'path': '/a'})]


def test_when_fence_body_is_malformed_json_then_skipped_silently():
    # Arrange — fence opens but body is not parseable.
    reply = (
        '```tool\n'
        '{not even close to json}\n'
        '```'
    )

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert calls == []
