"""Tier 1 interactive agent loop tests. See src-spec/tier1/ and tests-spec/tier1/."""
import pytest
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


def test_when_run_loop_produces_submission_then_solver_move_returns_one_of_wasd(
        tmp_path, vllm_base_url, vllm_api_key):
    from src.tier1.harness import load_submission
    # Arrange
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    env_dir = REPO / 'tasks/2048'
    tasks_dir = REPO / 'tasks'
    starting_board = [
        [2, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 2],
        [0, 0, 0, 0],
    ]

    # Act
    run_loop(workspace, env_dir, tasks_dir, vllm_base_url, vllm_api_key, max_iters=20)
    submission = workspace / 'submission.py'
    assert submission.exists(), 'submission.py not written during run_loop'
    module = load_submission(submission)
    solver = module.Solver()
    action = solver.move(starting_board)

    # Assert
    assert action in {'W', 'A', 'S', 'D'}, f'action={action!r} not in WASD'




def test_when_run_loop_called_with_condense_callable_then_condense_invoked_before_each_call_model(
        monkeypatch, tmp_path):
    """Cycle 15: pin the condense-callable seam in agent_loop.run_loop."""
    from src.tier1 import agent_loop
    # Arrange
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    env_dir = tmp_path / 'env'
    env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'
    tasks_dir.mkdir()

    finish_reply = (
        '```tool\n'
        '{"name": "finish", "args": {"note": "test stub"}}\n'
        '```'
    )
    monkeypatch.setattr(agent_loop, '_call_model',
                        lambda *args, **kwargs: finish_reply)

    calls = []
    def recording_condense(messages):
        calls.append(tuple(messages))
        return messages

    # Act
    agent_loop.run_loop(
        workspace=workspace,
        env_dir=env_dir,
        tasks_dir=tasks_dir,
        vllm_base_url='http://unused',
        vllm_api_key='unused',
        max_iters=1,
        condense=recording_condense,
    )

    # Assert
    assert len(calls) >= 1, f'condense not called; calls={len(calls)}'
    # First call receives at least the system + first-user messages
    first_call_messages = calls[0]
    assert isinstance(first_call_messages, tuple)
    assert len(first_call_messages) >= 2
    roles = [m['role'] for m in first_call_messages]
    assert 'system' in roles
    assert 'user' in roles



def test_when_supervisor_recommends_stop_then_run_loop_terminates_early(monkeypatch, tmp_path):
    """Cycle 33: pin supervisor-hook seam in run_loop.

    Stub supervisor returns stop_recommended=True on every judge call;
    with supervisor_every_k=1 the loop should exit after iter 1."""
    from src.tier1 import agent_loop as al
    from src.reward_bench.entities.supervisor_decision import SupervisorDecision

    # Arrange — stub model returns a syntactically-valid `view` tool call.
    call_counter = {'n': 0}
    def fake_call_model(*args, **kwargs):
        call_counter['n'] += 1
        return (
            "```tool\n"
            "{\"name\": \"view\", \"args\": {\"path\": \"/workspace\"}}\n"
            "```"
        )
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    class _StubStopSupervisor:
        def judge(self, sweep):
            return SupervisorDecision(
                plateau=True, stop_recommended=True, reasoning='stub stop',
            )

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    # Act
    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=10,
        supervisor=_StubStopSupervisor(),
        supervisor_every_k=1,
    )

    # Assert
    assert result['iterations'] == 1, (
        f"expected iter==1 (supervisor stopped after first), got "
        f"{result['iterations']}"
    )
    assert result['finished'] is True
    assert call_counter['n'] == 1
    last_msg_text = ''.join(
        m.get('content', '') for m in result['messages'][-3:]
    )
    assert 'stub stop' in last_msg_text, (
        f"supervisor reasoning not surfaced into final messages: "
        f"{last_msg_text!r}"
    )


def test_when_supervisor_every_k_zero_then_supervisor_not_consulted(monkeypatch, tmp_path):
    """Default supervisor_every_k=0 must keep cycle-12 behavior — supervisor
    is NEVER consulted, no behavior change for existing campaigns."""
    from src.tier1 import agent_loop as al
    from src.reward_bench.entities.supervisor_decision import SupervisorDecision

    # Arrange — model emits a finish call on the first turn so the loop
    # exits cleanly via the normal path, not via supervisor.
    def fake_call_model(*args, **kwargs):
        return (
            "```tool\n"
            "{\"name\": \"finish\", \"args\": {\"note\": \"done\"}}\n"
            "```"
        )
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    judge_counter = {'n': 0}
    class _CountingSupervisor:
        def judge(self, sweep):
            judge_counter['n'] += 1
            return SupervisorDecision(
                plateau=False, stop_recommended=False, reasoning='nope',
            )

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    # Act — pass a supervisor but leave supervisor_every_k at default (0).
    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=3,
        supervisor=_CountingSupervisor(),
    )

    # Assert — supervisor never asked.
    assert judge_counter['n'] == 0, (
        f"supervisor consulted {judge_counter['n']} times with k=0 default"
    )
    assert result['finished'] is True  # via the normal finish path



def test_when_dev_runner_output_observed_then_sample_recorded_into_supervisor_sweep(monkeypatch, tmp_path):
    """Cycle 34: pin dev_runner parser feeding real samples to supervisor."""
    from src.tier1 import agent_loop as al
    from src.reward_bench.entities.supervisor_decision import SupervisorDecision

    # Arrange — model emits a bash tool call; execute_tool returns a
    # dev_runner-shaped summary line.
    def fake_call_model(*args, **kwargs):
        return (
            "```tool\n"
            "{\"name\": \"bash\", "
            "\"args\": {\"cmd\": \"python3 /tasks/2048/dev_runner.py /workspace/submission.py\"}}\n"
            "```"
        )
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    def fake_execute_tool(name, args, *_, **__):
        return (
            "=== dev-runner ===\n"
            "  seed= 1  score=5000  max_tile= 512  moves=999  state=lost (1.5s)\n"
            "\n  MEAN=5000.0  MEDIAN=4800.0  max-tile-best=512  (1.5s total)"
        )
    monkeypatch.setattr(al, 'execute_tool', fake_execute_tool)

    captured = {'sweeps': []}
    class _RecordingSupervisor:
        def judge(self, sweep):
            captured['sweeps'].append(sweep)
            return SupervisorDecision(
                plateau=False, stop_recommended=False, reasoning='recorded',
            )

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    # Act
    al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=1,
        supervisor=_RecordingSupervisor(),
        supervisor_every_k=1,
    )

    # Assert
    assert len(captured['sweeps']) == 1, (
        f"supervisor consulted {len(captured['sweeps'])} times, expected 1"
    )
    sweep = captured['sweeps'][0]
    assert len(sweep) == 1, f"sweep len = {len(sweep)}, expected 1"
    iter_no, mean_score, max_tile, walltime_sec = sweep[0]
    assert iter_no == 1, f"iter_no={iter_no}"
    assert mean_score == 5000.0, f"mean_score={mean_score}"
    assert max_tile == 512, f"max_tile={max_tile}"
    assert walltime_sec == 1.5, f"walltime_sec={walltime_sec}"


def test_when_no_dev_runner_line_then_supervisor_sweep_has_placeholder_sample(monkeypatch, tmp_path):
    """No dev_runner output -> placeholder sample (preserves n_samples
    == iter_count). Sample fields are zero-filled."""
    from src.tier1 import agent_loop as al
    from src.reward_bench.entities.supervisor_decision import SupervisorDecision

    def fake_call_model(*args, **kwargs):
        return (
            "```tool\n"
            "{\"name\": \"view\", \"args\": {\"path\": \"/workspace\"}}\n"
            "```"
        )
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    captured = {'sweeps': []}
    class _RecordingSupervisor:
        def judge(self, sweep):
            captured['sweeps'].append(sweep)
            return SupervisorDecision(
                plateau=False, stop_recommended=False, reasoning='ok',
            )

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    # Act
    al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=1,
        supervisor=_RecordingSupervisor(),
        supervisor_every_k=1,
    )

    # Assert — exactly one placeholder sample with zeros
    sweep = captured['sweeps'][0]
    assert len(sweep) == 1
    iter_no, mean_score, max_tile, walltime_sec = sweep[0]
    assert iter_no == 1
    assert mean_score == 0.0
    assert max_tile == 0
    assert walltime_sec == 0.0



def test_when_max_no_tool_call_iters_exceeded_then_run_loop_terminates(monkeypatch, tmp_path):
    """Cycle 38: K consecutive no-tool-call iters break the loop."""
    from src.tier1 import agent_loop as al

    def fake_call_model(*args, **kwargs):
        return "I'm thinking about this but not emitting a tool block."
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=100,
        max_no_tool_call_iters=3,
    )

    assert result['iterations'] == 3, (
        f"expected stop at iter 3, got {result['iterations']}"
    )
    assert result['finished'] is False


def test_when_agent_loop_wall_sec_exceeded_then_run_loop_returns_partial_result(monkeypatch, tmp_path):
    """Cycle 38: wall-time budget mirrors score_submission.hard_wall_sec."""
    import time as _time
    from src.tier1 import agent_loop as al

    def fake_call_model(*args, **kwargs):
        _time.sleep(0.3)
        return (
            "```tool\n"
            "{\"name\": \"view\", \"args\": {\"path\": \"/workspace\"}}\n"
            "```"
        )
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=100,
        agent_loop_wall_sec=0.5,
    )

    assert result['iterations'] >= 1
    assert result['iterations'] < 100, (
        f"loop ran full budget; got {result['iterations']}"
    )
    assert result['finished'] is False



def test_when_first_user_inspected_then_includes_skill_spec_reference_and_active_tool_hint():
    """Cycle 61 supersedes cycle-39 literal-equality pin: shape contract.

    Per ADR 0008, FIRST_USER must (1) tell the model to read the SKILL
    spec, and (2) mention either the active execute_submission tool or
    the legacy /workspace/submission.py path. See
    tests-spec/tier1/agent_loop/test_spec_when_first_user_inspected_*."""
    from src.tier1.agent_loop import FIRST_USER

    # Requirement 1: must reference the SKILL spec file.
    assert '/tasks/2048/SKILL_tier1.md' in FIRST_USER, (
        f"FIRST_USER must instruct the model to read SKILL_tier1.md. "
        f"first 300 chars: {FIRST_USER[:300]!r}"
    )

    # Requirement 2: must hint at active (ADR 0008) OR legacy tool.
    mentions_active = 'execute_submission' in FIRST_USER
    mentions_legacy = '/workspace/submission.py' in FIRST_USER
    assert mentions_active or mentions_legacy, (
        f"FIRST_USER must mention either 'execute_submission' (active per "
        f"ADR 0008) or '/workspace/submission.py' (legacy). "
        f"first 300 chars: {FIRST_USER[:300]!r}"
    )

    # Requirement 3: reasonable length (not empty, not code stub injection).
    assert 50 <= len(FIRST_USER) <= 1200, (
        f"FIRST_USER length {len(FIRST_USER)} outside [50, 1200]"
    )



def test_when_run_loop_observes_new_best_dev_mean_then_snapshots_submission_for_restore_at_finish(monkeypatch, tmp_path):
    """Cycle 48 / hypothesis #1: best-snapshot + restore.

    Model regresses mid-trial: writes good submission, then worse one,
    then finishes. Active loop currently scores the LATEST = worse one.
    Legacy loop restores the best snapshot for scoring."""
    from src.tier1 import agent_loop as al

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()
    submission = workspace / 'submission.py'

    script = iter([
        # iter 1: write good
        '```tool\n{"name": "write_file", "args": {"path": "/workspace/submission.py"}}\n===FILE_BODY===\n# A\n```',
        # iter 2: run dev_runner (best MEAN=1000)
        '```tool\n{"name": "bash", "args": {"cmd": "python3 /tasks/2048/dev_runner.py /workspace/submission.py"}}\n```',
        # iter 3: write worse
        '```tool\n{"name": "write_file", "args": {"path": "/workspace/submission.py"}}\n===FILE_BODY===\n# B\n```',
        # iter 4: run dev_runner (MEAN=500, no new best)
        '```tool\n{"name": "bash", "args": {"cmd": "python3 /tasks/2048/dev_runner.py /workspace/submission.py"}}\n```',
        # iter 5: finish
        '```tool\n{"name": "finish", "args": {"note": "done"}}\n```',
    ])
    def fake_call_model(*args, **kwargs):
        return next(script)
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    dev_outs = iter([
        "  MEAN=1000.0  MEDIAN=1000.0  max-tile-best=256  (0.0s total)",
        "  MEAN=500.0  MEDIAN=500.0  max-tile-best=128  (0.0s total)",
    ])
    def fake_execute_tool(name, args, ws_arg, *_, **__):
        if name == 'write_file':
            (ws_arg / 'submission.py').write_text(args.get('content', ''))
            return '<ok>wrote</ok>'
        if name == 'bash':
            return next(dev_outs)
        if name == 'finish':
            return '<finish>ok</finish>'
        return '<ok>'
    monkeypatch.setattr(al, 'execute_tool', fake_execute_tool)

    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=10,
    )

    assert result['finished'] is True, f"loop should finish, got {result!r}"
    final = submission.read_text()
    assert final == '# A', (
        f"submission.py should be restored to best-snapshot '# A' at finish; "
        f"got {final!r}. Active loop scores LATEST, not best-MEAN snapshot."
    )
    best = workspace / 'submission.best.py'
    assert best.exists(), 'submission.best.py should have been written'
    assert best.read_text() == '# A'



def test_when_finish_called_below_finish_floor_then_rejected_and_loop_continues(monkeypatch, tmp_path):
    """Cycle 50 / hypothesis #2: finish-floor rejects premature finish."""
    from src.tier1 import agent_loop as al

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    script = iter([
        # iter 1: try to finish — should be rejected (no dev_runner yet)
        '```tool\n{"name": "finish", "args": {"note": "skipping"}}\n```',
        # iter 2: run dev_runner — MEAN=100 (below floor)
        '```tool\n{"name": "bash", "args": {"cmd": "python3 /tasks/2048/dev_runner.py /workspace/submission.py"}}\n```',
        # iter 3: try to finish — best=100 < floor=200, rejected
        '```tool\n{"name": "finish", "args": {"note": "good enough"}}\n```',
        # iter 4: run dev_runner — MEAN=500 (above floor)
        '```tool\n{"name": "bash", "args": {"cmd": "python3 /tasks/2048/dev_runner.py /workspace/submission.py"}}\n```',
        # iter 5: try to finish — best=500 > floor=200, accepted
        '```tool\n{"name": "finish", "args": {"note": "finally"}}\n```',
    ])
    def fake_call_model(*args, **kwargs):
        return next(script)
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    dev_outs = iter([
        "  MEAN=100.0  MEDIAN=100.0  max-tile-best=64  (0.0s total)",
        "  MEAN=500.0  MEDIAN=500.0  max-tile-best=256  (0.0s total)",
    ])
    def fake_execute_tool(name, args, ws_arg, *_, **__):
        if name == 'bash':
            return next(dev_outs)
        if name == 'finish':
            return '<finish>ok</finish>'
        return '<ok>'
    monkeypatch.setattr(al, 'execute_tool', fake_execute_tool)

    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=10,
        finish_floor=200.0,
    )

    assert result['iterations'] == 5, (
        f'loop should ran past 2 rejected finishes; got iter={result["iterations"]}'
    )
    assert result['finished'] is True
    # Check observations contain rejection.
    rejected_count = sum(
        1 for m in result['messages']
        if m['role'] == 'user' and 'finish rejected' in m.get('content', '')
    )
    assert rejected_count >= 1, (
        f'no finish-rejected observation found in messages; got {rejected_count}'
    )


def test_when_finish_floor_zero_then_any_finish_accepted(monkeypatch, tmp_path):
    """Default finish_floor=0 preserves cycle-12 behaviour — no rejection."""
    from src.tier1 import agent_loop as al

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    def fake_call_model(*args, **kwargs):
        return '```tool\n{"name": "finish", "args": {"note": "done"}}\n```'
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=10,
    )
    assert result['finished'] is True
    assert result['iterations'] == 1



def test_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising():
    """Cycle 51 / hypothesis #9: parse_tool_calls must be defensive."""
    from src.tier1.agent_loop import parse_tool_calls
    bad = (
        "```tool\n"
        '{"name": "view", "args": {"path": "/x"}}\n'
        "extra text after JSON\n"
        "```"
    )
    # Pre-fix this raises json.JSONDecodeError. Post-fix it returns [].
    out = parse_tool_calls(bad)
    assert out == [], f"expected [] from malformed block, got {out!r}"


def test_when_parse_tool_calls_given_trailing_comma_then_recovers_via_rstrip():
    """Legacy fallback: rstrip(', \\t\\n') lets trailing comma parse."""
    from src.tier1.agent_loop import parse_tool_calls
    body = (
        "```tool\n"
        '{"name": "view", "args": {"path": "/x"}},\n'  # trailing comma
        "```"
    )
    out = parse_tool_calls(body)
    assert len(out) == 1, f"expected 1 tool call (rstrip fallback), got {out!r}"
    assert out[0][0] == 'view'


def test_when_parse_tool_calls_given_non_dict_root_then_skipped():
    """Reply with `[1,2,3]` (not a dict) must skip, not crash."""
    from src.tier1.agent_loop import parse_tool_calls
    body = "```tool\n[1,2,3]\n```"
    out = parse_tool_calls(body)
    assert out == []



def test_when_call_model_invoked_then_max_tokens_matches_legacy_budget(monkeypatch):
    """Cycle 52 / hypothesis #7: _call_model uses max_tokens=12288."""
    import json
    from src.tier1 import agent_loop as al

    captured = {'payload': None}
    class _MockResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self):
            return b'{"choices":[{"message":{"content":"ok"}}]}'
    def fake_urlopen(req, timeout=600):
        captured['payload'] = json.loads(req.data.decode())
        return _MockResp()
    monkeypatch.setattr(al.urllib.request, 'urlopen', fake_urlopen)

    al._call_model('http://stub', 'stub', [{'role': 'user', 'content': 'hi'}])

    assert captured['payload'] is not None, 'urlopen not intercepted'
    assert captured['payload']['max_tokens'] == 12288, (
        f"max_tokens should be 12288 (legacy budget); got "
        f"{captured['payload']['max_tokens']}"
    )



@pytest.mark.live
def test_when_first_reply_received_then_views_skill_spec_or_writes_protocol_valid_solver(tmp_path):
    """Cycle 56: prompt validation. The active SYSTEM_PROMPT + FIRST_USER
    must drive the model to either view SKILL_tier1.md or write a
    protocol-valid Solver in its FIRST reply. RED-driven prompt engineering.
    """
    import os, subprocess
    from src.tier1.agent_loop import (
        SYSTEM_PROMPT, FIRST_USER, _call_model, parse_tool_calls,
    )
    from src.tier1.harness import load_submission, validate_submission_protocol

    api_key = os.environ.get('VLLM_API_KEY')
    if not api_key:
        pytest.skip('VLLM_API_KEY not set')
    # Resolve the active vLLM IP
    out = subprocess.run(
        ['docker', 'inspect', 'reward-bench-vllm', '--format',
         '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}'],
        capture_output=True, text=True,
    )
    ip = out.stdout.strip()
    if not ip:
        pytest.skip('reward-bench-vllm container not running')
    base_url = f'http://{ip}:8000'

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': FIRST_USER},
    ]
    reply = _call_model(base_url, api_key, messages, temperature=0.0)
    tool_calls = parse_tool_calls(reply)

    assert tool_calls, (
        f'First reply emitted no parseable tool calls. Prompt is broken. '
        f'Reply (first 500 chars): {reply[:500]!r}'
    )
    name, args = tool_calls[0]

    if name == 'view' and args.get('path') == '/tasks/2048/SKILL_tier1.md':
        return  # Model is reading the spec — good behaviour.

    if name == 'execute_submission':
        # ADR 0008 active path: body inline, no path argument.
        body = args.get('content', '')
        sub = tmp_path / 'submission.py'
        sub.write_text(body)
        try:
            mod = load_submission(sub)
        except SyntaxError as e:
            pytest.fail(
                f'First execute_submission body had SyntaxError: {e}. '
                f'Prompt is broken.'
            )
        violations = validate_submission_protocol(mod)
        assert violations == (), (
            f'First execute_submission body violates SKILL_tier1.md '
            f'protocol. Violations: {violations}. Prompt is broken.'
        )
        return

    if name == 'write_file' and args.get('path') == '/workspace/submission.py':
        body = args.get('content', '')
        sub = tmp_path / 'submission.py'
        sub.write_text(body)
        try:
            mod = load_submission(sub)
        except SyntaxError as e:
            pytest.fail(
                f'First reply wrote submission.py with SyntaxError: {e}. '
                f'Prompt is broken.'
            )
        violations = validate_submission_protocol(mod)
        assert violations == (), (
            f'First reply wrote a submission that violates SKILL_tier1.md '
            f'protocol. Violations: {violations}. Prompt is broken.'
        )
        return

    pytest.fail(
        f'First reply neither views /tasks/2048/SKILL_tier1.md nor writes a '
        f'protocol-valid /workspace/submission.py. '
        f'Got: name={name!r} args={args!r}. Prompt is broken.'
    )



@pytest.mark.live
def test_when_first_reply_at_campaign_temperature_then_majority_views_skill_or_writes_valid_solver(tmp_path):
    """Cycle 56 (campaign-T variant): repeat the same assertion at
    temperature=0.7 (campaign default per ADR 0003) across N=5 trials.
    Assert at least 3/5 pass. This is what the actual campaign sees.
    """
    import os, subprocess
    from src.tier1.agent_loop import (
        SYSTEM_PROMPT, FIRST_USER, _call_model, parse_tool_calls,
    )
    from src.tier1.harness import load_submission, validate_submission_protocol
    api_key = os.environ.get('VLLM_API_KEY')
    if not api_key:
        pytest.skip('VLLM_API_KEY not set')
    out = subprocess.run(
        ['docker', 'inspect', 'reward-bench-vllm', '--format',
         '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}'],
        capture_output=True, text=True,
    )
    ip = out.stdout.strip()
    if not ip:
        pytest.skip('reward-bench-vllm container not running')
    base_url = f'http://{ip}:8000'
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': FIRST_USER},
    ]
    passes = []
    failures = []
    for trial in range(5):
        reply = _call_model(base_url, api_key, messages, temperature=0.7)
        tool_calls = parse_tool_calls(reply)
        if not tool_calls:
            failures.append(f'trial {trial}: no tool calls')
            continue
        name, args = tool_calls[0]
        if name == 'view' and args.get('path') == '/tasks/2048/SKILL_tier1.md':
            passes.append(trial)
            continue
        if name == 'execute_submission':
            body = args.get('content', '')
            sub = tmp_path / f'execsub_t{trial}.py'
            sub.write_text(body)
            try:
                mod = load_submission(sub)
                violations = validate_submission_protocol(mod)
                if violations == ():
                    passes.append(trial)
                    continue
                failures.append(
                    f'trial {trial}: execute_submission violations={violations}'
                )
            except SyntaxError as e:
                failures.append(f'trial {trial}: execute_submission SyntaxError {e}')
            continue
        if name == 'write_file' and args.get('path') == '/workspace/submission.py':
            body = args.get('content', '')
            sub = tmp_path / f'submission_t{trial}.py'
            sub.write_text(body)
            try:
                mod = load_submission(sub)
                violations = validate_submission_protocol(mod)
                if violations == ():
                    passes.append(trial)
                    continue
                failures.append(
                    f'trial {trial}: write_file violations={violations}'
                )
            except SyntaxError as e:
                failures.append(f'trial {trial}: SyntaxError {e}')
            continue
        failures.append(
            f'trial {trial}: first call name={name!r} args={args!r}'
        )
    assert len(passes) >= 3, (
        f'At T=0.7 only {len(passes)}/5 first-replies are protocol-correct. '
        f'Prompt is unreliable at campaign temperature. '
        f'passes={passes} failures={failures}'
    )



def test_when_execute_submission_called_with_valid_solver_body_then_returns_per_seed_observation(tmp_path):
    """Cycle 58: pin the happy-path execute_submission observation."""
    import json
    from src.tier1.agent_loop import execute_tool

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    # Use the real tasks/2048 for the dev_runner the dispatcher invokes.
    from pathlib import Path as _P
    tasks_dir = _P('/home/vmihaylov/forge/phase-c-information-systems-architecture/'
                   'application-architecture/reward-bench/tasks')
    if not tasks_dir.exists():
        pytest.skip('tasks/ not present in this sandbox')

    body = (
        "class Solver:\n"
        "    def __init__(self): pass\n"
        "    def move(self, board):\n"
        "        return 'W'\n"
    )

    obs = execute_tool('execute_submission', {'content': body},
                        workspace, env_dir, tasks_dir)
    # Strip any surrounding tags and parse the JSON.
    body_json = obs
    if body_json.startswith('<observation>') and body_json.endswith('</observation>'):
        body_json = body_json[len('<observation>'):-len('</observation>')]
    payload = json.loads(body_json.strip())

    assert payload['protocol_violations'] == [], (
        f'valid Solver should yield no violations; got {payload["protocol_violations"]}'
    )
    assert isinstance(payload['per_seed'], list)
    assert len(payload['per_seed']) >= 1, 'dev seeds should have produced at least one game'
    for entry in payload['per_seed']:
        for key in ('seed', 'score', 'max_tile', 'moves', 'state', 'walltime_sec'):
            assert key in entry, f'per_seed entry missing {key}'
    assert payload['mean'] == payload['mean']  # not NaN
    assert payload['mean'] >= 0
    assert payload['max_tile_best'] >= 2


def test_when_execute_submission_called_with_gym_style_body_then_observation_has_protocol_violation(tmp_path):
    """Cycle 58: pin the Gym-style failure into structured observation."""
    import json
    from src.tier1.agent_loop import execute_tool
    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    from pathlib import Path as _P
    tasks_dir = _P('/home/vmihaylov/forge/phase-c-information-systems-architecture/'
                   'application-architecture/reward-bench/tasks')
    if not tasks_dir.exists():
        pytest.skip('tasks/ not present in this sandbox')

    body = (
        "def solve(state):\n"
        "    return 0\n"
    )
    obs = execute_tool('execute_submission', {'content': body},
                        workspace, env_dir, tasks_dir)
    body_json = obs
    if body_json.startswith('<observation>') and body_json.endswith('</observation>'):
        body_json = body_json[len('<observation>'):-len('</observation>')]
    payload = json.loads(body_json.strip())
    assert len(payload['protocol_violations']) >= 1, (
        f'Gym-style should be flagged; got {payload}'
    )
    assert any('Solver' in v for v in payload['protocol_violations'])
    assert payload['per_seed'] == []
    assert payload['mean'] == 0


def test_when_execute_submission_called_with_syntax_error_body_then_observation_has_syntax_violation(tmp_path):
    """Cycle 58: pin the SyntaxError failure into structured observation."""
    import json
    from src.tier1.agent_loop import execute_tool
    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    from pathlib import Path as _P
    tasks_dir = _P('/home/vmihaylov/forge/phase-c-information-systems-architecture/'
                   'application-architecture/reward-bench/tasks')
    if not tasks_dir.exists():
        pytest.skip('tasks/ not present in this sandbox')

    body = 'class Solver: def __init__(self): pass def move(self, board): return W\n'  # broken
    obs = execute_tool('execute_submission', {'content': body},
                        workspace, env_dir, tasks_dir)
    body_json = obs
    if body_json.startswith('<observation>') and body_json.endswith('</observation>'):
        body_json = body_json[len('<observation>'):-len('</observation>')]
    payload = json.loads(body_json.strip())
    assert any('SyntaxError' in v for v in payload['protocol_violations']), (
        f'SyntaxError should be flagged; got {payload}'
    )
    assert payload['per_seed'] == []
    assert payload['mean'] == 0



def test_when_execute_submission_observation_observed_then_mean_feeds_best_dev_mean_tracker(monkeypatch, tmp_path):
    """Cycle 63: pin active-path equivalent of cycle-34 parser."""
    from src.tier1 import agent_loop as al
    from src.reward_bench.entities.supervisor_decision import SupervisorDecision

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()
    (workspace / 'submission.py').write_text('# placeholder')

    script = iter([
        # iter 1: execute_submission returning mean=1000
        '```tool\n{"name": "execute_submission", "args": {}}\n===FILE_BODY===\n# code v1\n```',
        # iter 2: execute_submission returning mean=500 (worse)
        '```tool\n{"name": "execute_submission", "args": {}}\n===FILE_BODY===\n# code v2\n```',
        # iter 3: finish
        '```tool\n{"name": "finish", "args": {"note": "done"}}\n```',
    ])
    def fake_call_model(*args, **kwargs):
        return next(script)
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    obs_iter = iter([
        '<observation>{"protocol_violations": [], "per_seed": [{"seed":1,"score":1000,"max_tile":256}], "mean": 1000.0, "median": 1000, "max_tile_best": 256, "walltime_sec_total": 1.5}</observation>',
        '<observation>{"protocol_violations": [], "per_seed": [{"seed":1,"score":500,"max_tile":128}], "mean": 500.0, "median": 500, "max_tile_best": 128, "walltime_sec_total": 0.8}</observation>',
    ])
    def fake_execute_tool(name, args, ws_arg, *_, **__):
        if name == 'execute_submission':
            return next(obs_iter)
        if name == 'finish':
            return '<finish>ok</finish>'
        return '<ok>'
    monkeypatch.setattr(al, 'execute_tool', fake_execute_tool)

    captured = {'sweeps': []}
    class _RecordingSupervisor:
        def judge(self, sweep):
            captured['sweeps'].append(sweep)
            return SupervisorDecision(
                plateau=False, stop_recommended=False, reasoning='ok',
            )

    al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=10,
        supervisor=_RecordingSupervisor(),
        supervisor_every_k=1,
    )

    # Cycle 34 sweep contract: each iter's sample is in the latest sweep.
    assert captured['sweeps'], 'supervisor never called'
    last_sweep = captured['sweeps'][-1]
    means = [s[1] for s in last_sweep]
    assert 1000.0 in means, f'1000.0 not in sweep means {means} — active parser silent'
    assert 500.0 in means, f'500.0 not in sweep means {means}'

    # Cycle 48 best-snapshot: workspace/submission.best.py should exist
    # because we observed a new best (1000) on iter 1.
    best_path = workspace / 'submission.best.py'
    assert best_path.exists(), 'cycle-48 best-snapshot did not fire — best_dev_mean was never set'



def test_when_finish_called_below_finish_floor_via_execute_submission_then_rejected_and_loop_continues(monkeypatch, tmp_path):
    """Cycle 64: finish-floor via the ADR-0008 active data source.

    Mirrors cycle-50's finish-floor test but uses execute_submission's
    JSON observation (mean field) instead of bash dev_runner stdout."""
    from src.tier1 import agent_loop as al

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()
    (workspace / 'submission.py').write_text('# placeholder')

    script = iter([
        # iter 1: finish — no prior execute_submission, best unknown
        '```tool\n{"name": "finish", "args": {"note": "skipping"}}\n```',
        # iter 2: execute_submission with mean=100 (below floor)
        '```tool\n{"name": "execute_submission", "args": {}}\n===FILE_BODY===\n# v1\n```',
        # iter 3: finish — best=100 < floor=200, rejected
        '```tool\n{"name": "finish", "args": {"note": "good enough"}}\n```',
        # iter 4: execute_submission with mean=500 (above floor)
        '```tool\n{"name": "execute_submission", "args": {}}\n===FILE_BODY===\n# v2\n```',
        # iter 5: finish — best=500 > floor=200, accepted
        '```tool\n{"name": "finish", "args": {"note": "finally"}}\n```',
    ])
    def fake_call_model(*args, **kwargs):
        return next(script)
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    obs_iter = iter([
        '<observation>{"protocol_violations": [], "per_seed": [{"seed":1,"score":100,"max_tile":64}], "mean": 100.0, "median": 100, "max_tile_best": 64, "walltime_sec_total": 0.3}</observation>',
        '<observation>{"protocol_violations": [], "per_seed": [{"seed":1,"score":500,"max_tile":256}], "mean": 500.0, "median": 500, "max_tile_best": 256, "walltime_sec_total": 0.5}</observation>',
    ])
    def fake_execute_tool(name, args, ws_arg, *_, **__):
        if name == 'execute_submission':
            return next(obs_iter)
        if name == 'finish':
            return '<finish>ok</finish>'
        return '<ok>'
    monkeypatch.setattr(al, 'execute_tool', fake_execute_tool)

    result = al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=10,
        finish_floor=200.0,
    )

    assert result['iterations'] == 5, (
        f'expected stop at iter 5 (2 rejected finishes + accepted); '
        f'got iter={result["iterations"]}'
    )
    assert result['finished'] is True
    rejected_count = sum(
        1 for m in result['messages']
        if m['role'] == 'user' and 'finish rejected' in m.get('content', '')
    )
    assert rejected_count >= 2, (
        f'expected at least 2 finish-rejected observations; got {rejected_count}'
    )



def test_when_loop_ends_then_last_successful_execute_submission_body_promoted_to_workspace_submission_py(monkeypatch, tmp_path):
    """Cycle 65 / ADR 0008 finish-time promotion: the last successful
    execute_submission body becomes workspace/submission.py at finish."""
    from src.tier1 import agent_loop as al

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()

    GOOD = '# good body v1\nclass Solver:\n    def move(self, b): return "W"\n'
    BAD = '# bad body v2 (no Solver class)\ndef solve(grid): return 0\n'

    script = iter([
        '```tool\n{"name": "execute_submission", "args": {}}\n===FILE_BODY===\n' + GOOD + '```',
        '```tool\n{"name": "execute_submission", "args": {}}\n===FILE_BODY===\n' + BAD + '```',
        '```tool\n{"name": "finish", "args": {"note": "done"}}\n```',
    ])
    def fake_call_model(*args, **kwargs):
        return next(script)
    monkeypatch.setattr(al, '_call_model', fake_call_model)

    obs_iter = iter([
        '<observation>{"protocol_violations": [], "per_seed": [{"seed":1,"score":1000,"max_tile":256}], "mean": 1000.0, "median": 1000, "max_tile_best": 256, "walltime_sec_total": 0.5}</observation>',
        '<observation>{"protocol_violations": ["no Solver class"], "per_seed": [], "mean": 0.0, "median": 0, "max_tile_best": 0, "walltime_sec_total": 0.0}</observation>',
    ])
    def fake_execute_tool(name, args, ws_arg, *_, **__):
        if name == 'execute_submission':
            return next(obs_iter)
        if name == 'finish':
            return '<finish>ok</finish>'
        return '<ok>'
    monkeypatch.setattr(al, 'execute_tool', fake_execute_tool)

    al.run_loop(
        workspace=workspace, env_dir=env_dir, tasks_dir=tasks_dir,
        vllm_base_url='http://stub', vllm_api_key='stub',
        max_iters=10,
    )

    sub = workspace / 'submission.py'
    assert sub.exists(), 'finish-time promotion did not write submission.py'
    actual = sub.read_text()
    assert actual == GOOD, (
        f'expected GOOD body (last successful execute_submission); got:\n'
        f'{actual!r}'
    )



def test_when_system_prompt_inspected_then_advertises_execute_submission_as_primary_tool():
    """Cycle 66: per ADR 0008, SYSTEM_PROMPT must advertise execute_submission."""
    from src.tier1.agent_loop import SYSTEM_PROMPT

    # Required tool advertisements
    assert 'execute_submission' in SYSTEM_PROMPT, (
        "SYSTEM_PROMPT must advertise execute_submission per ADR 0008. "
        f"first 200 chars: {SYSTEM_PROMPT[:200]!r}"
    )
    assert 'view' in SYSTEM_PROMPT, 'SYSTEM_PROMPT must advertise view'
    assert 'finish' in SYSTEM_PROMPT, 'SYSTEM_PROMPT must advertise finish'

    # Required spec pointer
    assert '/tasks/2048/SKILL_tier1.md' in SYSTEM_PROMPT, (
        'SYSTEM_PROMPT must point the model at the SKILL spec file'
    )

    # Length sanity
    assert 1000 <= len(SYSTEM_PROMPT) <= 6000, (
        f'SYSTEM_PROMPT length {len(SYSTEM_PROMPT)} outside [1000, 6000]'
    )


def test_when_execute_submission_called_with_slow_solver_then_per_seed_reports_walltime_exceeded(tmp_path, monkeypatch):
    """Cycle 70: dev-path inherits wall-time protection via canonical scorer.

    Real-world repro from cycle 69 verification bench: model wrote
    expectimax(depth=4) Solver; _execute_submission's inline game loop
    wedged for hours. Now delegates to score_submission which has
    cycle 23 hard_wall_sec + cycle 27 per-game daemon-thread timeout
    + cycle 28/29 sentinels. The wedge is impossible by construction."""
    import json
    import time
    from src.tier1 import agent_loop
    from src.tier1.agent_loop import execute_tool

    # Shrink the dev wall-time cap so the test stays fast.
    monkeypatch.setattr(agent_loop, 'DEV_HARD_WALL_S', 0.5)

    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    from pathlib import Path as _P
    tasks_dir = _P(
        '/home/vmihaylov/forge/phase-c-information-systems-architecture/'
        'application-architecture/reward-bench/tasks'
    )
    if not tasks_dir.exists():
        pytest.skip('tasks/ not present in this sandbox')

    # Sleep is conditional: validate_submission_protocol calls move() once
    # on an empty board; sleeping there would dominate the test wall-time.
    # Sleep only when called with a non-empty board (i.e. inside a real game).
    body = (
        'import time\n'
        'class Solver:\n'
        '    def __init__(self): pass\n'
        '    def move(self, board):\n'
        '        if any(any(row) for row in board):\n'
        '            time.sleep(2.0)\n'
        "        return 'S'\n"
    )

    t0 = time.monotonic()
    obs = execute_tool('execute_submission', {'content': body},
                       workspace, env_dir, tasks_dir)
    elapsed = time.monotonic() - t0

    # Bounded wall-time. Without cycle 70 this wedges for many seconds
    # per move x many moves x 5 seeds. With cycle 70 + DEV_HARD_WALL_S=0.5
    # the canonical scorer sentinels the first game (daemon thread join
    # times out), all later seeds get walltime_exceeded immediately.
    assert elapsed < 15.0, (
        f'execute_submission took {elapsed:.1f}s, should be bounded '
        f'by DEV_HARD_WALL_S + abandoned-thread slack'
    )

    body_json = obs
    if body_json.startswith('<observation>') and body_json.endswith('</observation>'):
        body_json = body_json[len('<observation>'):-len('</observation>')]
    payload = json.loads(body_json.strip())

    assert payload['protocol_violations'] == [], (
        f"slow Solver is protocol-valid; got {payload['protocol_violations']}"
    )
    assert isinstance(payload['per_seed'], list)
    assert len(payload['per_seed']) >= 1
    states = [s['state'] for s in payload['per_seed']]
    walltime_exceeded = [s for s in payload['per_seed']
                         if s['state'] == 'walltime_exceeded']
    assert len(walltime_exceeded) >= 1, (
        f'expected >=1 walltime_exceeded sentinel; got states={states}'
    )

    # Schema preserved for cycle-63 parser.
    assert isinstance(payload['mean'], (int, float))
    assert payload['mean'] == payload['mean']  # not NaN
    assert isinstance(payload['max_tile_best'], int)



def test_when_call_model_invoked_then_payload_model_field_matches_served_name(monkeypatch):
    """Cycle 74: _call_model must use model_id in the payload, not the
    hardcoded cycle-11 'qwen3.6-27b-awq'.

    Real-world repro: cycle 72 smoke after cycle 73 fix. Container
    swapped to qwen3.6-27b-fp8; payload still said 'qwen3.6-27b-awq';
    vLLM returned HTTP 404."""
    import io
    import json as _json
    import urllib.request

    from src.tier1 import agent_loop

    captured = {}

    class _StopHere(RuntimeError):
        pass

    class _FakeResponse:
        def __init__(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            # Return a minimally valid chat-completion response so
            # the caller doesn't crash on the parse, but we'll
            # short-circuit before this with the captured payload.
            return _json.dumps({
                "choices": [{"message": {"content": "ok"}}]
            }).encode()

    def fake_urlopen(req, timeout=None):
        captured["data"] = req.data
        return _FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    out = agent_loop._call_model(
        vllm_base_url="http://stub",
        vllm_api_key="k",
        messages=[{"role": "user", "content": "hi"}],
        model_id="qwen3.6-27b-fp8",
    )

    assert "data" in captured, "_call_model did not call urlopen"
    payload = _json.loads(captured["data"].decode())
    assert payload["model"] == "qwen3.6-27b-fp8", (
        f"_call_model put model={payload['model']!r} in payload; "
        f"should have used the model_id kwarg"
    )

    # Back-compat: default keeps cycle-11 historical value so old
    # callers (some tests) don't break silently.
    sig = agent_loop._call_model.__defaults__
    assert "qwen3.6-27b-awq" in sig or any(
        "qwen3.6-27b-awq" == d for d in sig
    ), f"cycle-74 changed the default model_id; expected back-compat"
