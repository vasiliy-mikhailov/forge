"""Tier 1 interactive agent loop tests. See src-spec/tier1/ and tests-spec/tier1/."""
import json
import urllib.request

from src.tier1.agent_loop import SYSTEM_PROMPT, FIRST_USER, parse_tool_calls


def test_when_skill_prompt_sent_with_tool_protocol_then_reply_contains_tool_call_block(
        vllm_base_url, vllm_api_key):
    # Arrange
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': FIRST_USER},
        ],
        'max_tokens': 32768,
        'temperature': 0.0,
    }).encode()
    req = urllib.request.Request(
        f'{vllm_base_url}/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {vllm_api_key}',
        },
    )

    # Act
    with urllib.request.urlopen(req, timeout=600) as r:
        status = r.status
        data = json.loads(r.read())
    reply = data['choices'][0]['message']['content']

    # Assert
    assert status == 200
    assert '```tool' in reply, f'no fenced tool block in reply tail: {reply[-300:]!r}'


def test_when_tool_block_parsed_then_yields_name_and_args(tool_protocol_reply):
    # Arrange (tool_protocol_reply fixture is a real model reply)

    # Act
    calls = parse_tool_calls(tool_protocol_reply)

    # Assert
    assert len(calls) >= 1, f'no tool calls parsed from reply: {tool_protocol_reply!r}'
    name, args = calls[0]
    assert isinstance(name, str) and name, f'name not a non-empty string: {name!r}'
    assert isinstance(args, dict), f'args not a dict: {args!r}'
