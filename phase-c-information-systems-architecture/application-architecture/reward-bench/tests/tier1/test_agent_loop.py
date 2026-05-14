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



def test_when_first_user_inspected_then_matches_bak_freeform_variant():
    """Cycle 39: pin FIRST_USER to _bak's freeform variant.

    See tests-spec/tier1/agent_loop/test_spec_when_first_user_inspected_*."""
    from src.tier1.agent_loop import FIRST_USER

    expected = (
        "Start the task. Read /tasks/2048/SKILL_tier1.md to learn the "
        "constraints, then optionally /env/env_2048.py for env details, "
        "then write your submission to /workspace/submission.py and iterate. "
        "Use the fenced-block JSON tool format the system prompt described."
    )
    assert FIRST_USER == expected, (
        f"FIRST_USER drifted from _bak freeform variant.\n"
        f"len(actual)={len(FIRST_USER)} len(expected)={len(expected)}\n"
        f"first 200 chars actual: {FIRST_USER[:200]!r}"
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
