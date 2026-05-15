"""Cycle 98a / ADR 0011: contract tests for the three ProtocolParser adapters."""
from __future__ import annotations

from src.adapters.parsers.composite_parser import CompositeParser
from src.adapters.parsers.fenced_text_parser import FencedTextParser
from src.adapters.parsers.structured_openai_parser import StructuredOpenAIParser
from src.ports.protocol_parser import AssistantReply


def _reply(content: str = '', tool_calls: list | None = None) -> AssistantReply:
    return {'content': content, 'tool_calls': tool_calls or []}


# ---------------------------------------------------------------
# FencedTextParser — cycle 9/58 surface
# ---------------------------------------------------------------

def test_when_fenced_text_parser_given_one_block_then_extracts_one_call():
    reply = _reply(content=(
        '```tool\n'
        '{"name": "view", "args": {"path": "/tasks/2048/SKILL_tier1.md"}}\n'
        '```'
    ))
    calls = FencedTextParser().extract(reply)
    assert len(calls) == 1
    assert calls[0].name == 'view'
    assert calls[0].args == {'path': '/tasks/2048/SKILL_tier1.md'}


def test_when_fenced_text_parser_given_filebody_then_content_merged_into_args():
    reply = _reply(content=(
        '```tool\n'
        '{"name": "execute_submission", "args": {}}\n'
        '===FILE_BODY===\n'
        'class Solver: pass\n'
        '```'
    ))
    calls = FencedTextParser().extract(reply)
    assert len(calls) == 1
    assert calls[0].name == 'execute_submission'
    assert calls[0].args['content'].startswith('class Solver')


def test_when_fenced_text_parser_given_malformed_json_then_skips_block_silently():
    """Cycle 51 / hypothesis #9 — defensive parser must not raise."""
    reply = _reply(content='```tool\n{this is not json\n```')
    assert FencedTextParser().extract(reply) == []


def test_when_fenced_text_parser_given_no_blocks_then_returns_empty():
    assert FencedTextParser().extract(_reply(content='just prose')) == []


# ---------------------------------------------------------------
# StructuredOpenAIParser — cycle 83/96 surface
# ---------------------------------------------------------------

def test_when_structured_parser_given_one_call_then_extracts():
    reply = _reply(tool_calls=[{
        'id': 'x', 'type': 'function',
        'function': {'name': 'view',
                     'arguments': '{"path": "/tasks/2048/SKILL_tier1.md"}'},
    }])
    calls = StructuredOpenAIParser().extract(reply)
    assert len(calls) == 1
    assert calls[0].name == 'view'
    assert calls[0].args == {'path': '/tasks/2048/SKILL_tier1.md'}


def test_when_structured_parser_arguments_contain_sentencepiece_space_then_stripped():
    """Cycle 96: vLLM mistral leaks U+0120 / U+2581 into the JSON."""
    reply = _reply(tool_calls=[{
        'type': 'function',
        'function': {'name': 'view',
                     'arguments': '{"path":Ġ"SKILL_tier1.md"}'},
    }])
    calls = StructuredOpenAIParser().extract(reply)
    assert calls == [('view', {'path': 'SKILL_tier1.md'})]


def test_when_structured_parser_arguments_malformed_then_args_empty():
    reply = _reply(tool_calls=[{
        'type': 'function',
        'function': {'name': 'view', 'arguments': '{not json'},
    }])
    assert StructuredOpenAIParser().extract(reply) == [('view', {})]


def test_when_structured_parser_arguments_is_dict_then_used_directly():
    """Some vLLM modes emit arguments as a dict (non-strict)."""
    reply = _reply(tool_calls=[{
        'type': 'function',
        'function': {'name': 'finish', 'arguments': {'note': 'done'}},
    }])
    assert StructuredOpenAIParser().extract(reply) == [('finish', {'note': 'done'})]


# ---------------------------------------------------------------
# CompositeParser — fenced wins when both present
# ---------------------------------------------------------------

def test_when_composite_given_fenced_block_then_skips_structured():
    """Cycle 96 contract: fenced text is the default; structured is fallback."""
    reply = _reply(
        content=(
            '```tool\n'
            '{"name": "execute_submission", "args": {}}\n'
            '===FILE_BODY===\n# fenced\n```'
        ),
        tool_calls=[{
            'type': 'function',
            'function': {'name': 'finish',
                         'arguments': '{"note": "from structured"}'},
        }],
    )
    parser = CompositeParser([FencedTextParser(), StructuredOpenAIParser()])
    calls = parser.extract(reply)
    assert len(calls) == 1
    assert calls[0].name == 'execute_submission'


def test_when_composite_given_no_fenced_then_falls_back_to_structured():
    reply = _reply(content='', tool_calls=[{
        'type': 'function',
        'function': {'name': 'view', 'arguments': '{"path": "/x"}'},
    }])
    parser = CompositeParser([FencedTextParser(), StructuredOpenAIParser()])
    calls = parser.extract(reply)
    assert len(calls) == 1
    assert calls[0].name == 'view'


def test_when_composite_given_neither_then_returns_empty():
    parser = CompositeParser([FencedTextParser(), StructuredOpenAIParser()])
    assert parser.extract(_reply()) == []
