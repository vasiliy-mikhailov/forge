"""Tier 1 interactive agent loop tests. See src-spec/tier1/ and tests-spec/tier1/."""
import json
import tempfile
import urllib.request
from pathlib import Path

from src.tier1.agent_loop import (
    SYSTEM_PROMPT,
    FIRST_USER,
    parse_tool_calls,
    execute_tool,
    run_loop,
)


REPO = Path(__file__).resolve().parents[2]


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


def test_when_tool_block_has_file_body_then_content_extracted_into_args():
    # Arrange — production-shape reply (per SYSTEM_PROMPT contract).
    reply = (
        '```tool\n'
        '{"name": "write_file", "args": {"path": "/workspace/submission.py"}}\n'
        '===FILE_BODY===\n'
        'from __future__ import annotations\n'
        'SOLVER = 42\n'
        '```'
    )

    # Act
    calls = parse_tool_calls(reply)

    # Assert
    assert len(calls) == 1
    name, args = calls[0]
    assert name == 'write_file'
    assert args['path'] == '/workspace/submission.py'
    assert args['content'].startswith('from __future__ import annotations'), (
        f'content unexpected: {args.get("content")!r}'
    )


def test_when_view_tool_executed_then_returns_file_contents(tmp_path):
    # Arrange
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    env_dir = REPO / 'tasks/2048'    # env_2048.py lives alongside tasks
    tasks_dir = REPO / 'tasks'
    args = {'path': '/tasks/2048/SKILL_tier1.md'}

    # Act
    result = execute_tool('view', args, workspace, env_dir, tasks_dir)

    # Assert
    assert '<view path="/tasks/2048/SKILL_tier1.md">' in result, f'view header missing: {result[:200]!r}'
    skill_head = (REPO / 'tasks/2048/SKILL_tier1.md').read_text()[:50]
    assert skill_head in result, f'file head not in observation: {result[:300]!r}'


def test_when_write_file_tool_executed_then_writes_to_workspace(tmp_path):
    # Arrange
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    env_dir = REPO / 'tasks/2048'
    tasks_dir = REPO / 'tasks'
    content = "from __future__ import annotations\nVALUE = 42\n"
    args = {'path': '/workspace/submission.py', 'content': content}

    # Act
    result = execute_tool('write_file', args, workspace, env_dir, tasks_dir)

    # Assert
    target = workspace / 'submission.py'
    assert target.exists(), f'file not written; observation: {result!r}'
    assert target.read_text() == content, f'contents differ; observation: {result!r}'
    assert '<ok>' in result and '/workspace/submission.py' in result, f'unexpected observation: {result!r}'


def test_when_finish_tool_executed_then_returns_finish_signal(tmp_path):
    # Arrange
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    env_dir = REPO / 'tasks/2048'
    tasks_dir = REPO / 'tasks'
    args = {'note': 'all done'}

    # Act
    result = execute_tool('finish', args, workspace, env_dir, tasks_dir)

    # Assert
    assert result.startswith('<finish>') and result.endswith('</finish>'), f'unexpected: {result!r}'
    assert 'all done' in result, f'note missing: {result!r}'


def test_when_bash_tool_executed_with_allowed_cmd_then_returns_stdout(tmp_path):
    # Arrange
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    # Put a sentinel file in workspace so `ls /workspace` has output.
    (workspace / 'submission.py').write_text('# sentinel\n')
    env_dir = REPO / 'tasks/2048'
    tasks_dir = REPO / 'tasks'
    args = {'cmd': 'ls /workspace'}

    # Act
    result = execute_tool('bash', args, workspace, env_dir, tasks_dir)

    # Assert
    assert '<bash exit=0>' in result, f'no successful bash header: {result!r}'
    assert '--- stdout ---' in result, f'no stdout section: {result!r}'
    assert 'submission.py' in result, f'sentinel not in stdout: {result!r}'


def test_when_run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history(
        tmp_path, vllm_base_url, vllm_api_key):
    # Arrange
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    env_dir = REPO / 'tasks/2048'
    tasks_dir = REPO / 'tasks'

    # Act
    result = run_loop(workspace, env_dir, tasks_dir, vllm_base_url, vllm_api_key, max_iters=1)

    # Assert
    assert result['iterations'] == 1, f'iterations={result["iterations"]}'
    msgs = result['messages']
    assert len(msgs) == 4, f'expected 4 messages, got {len(msgs)}: roles={[m["role"] for m in msgs]}'
    observation = msgs[-1]['content']
    assert '<view path=' in observation or '<error>' in observation, (
        f'observation has neither view nor error: {observation[:300]!r}'
    )


