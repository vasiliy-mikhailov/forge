import pytest
"""Tier 1 end-to-end tests against live qwen3.6-27b-awq.
See src-spec/tier1/ (per-behavior src_spec_when_*.md files).
See tests-spec/tier1/ (per-behavior test_spec_when_*.md files)."""
import json
import urllib.request


def _get_models(base_url, api_key, timeout=10):
    req = urllib.request.Request(
        f'{base_url}/v1/models',
        headers={'Authorization': f'Bearer {api_key}'},
    )
    return urllib.request.urlopen(req, timeout=timeout)


def test_when_vllm_container_serves_then_v1_models_endpoint_responds(vllm_base_url, vllm_api_key):
    # Arrange (vllm_base_url fixture has already ensured serving)

    # Act
    with _get_models(vllm_base_url, vllm_api_key) as r:
        status = r.status
        body = r.read()

    # Assert
    assert status == 200
    assert body, 'empty body from /v1/models'


def test_when_v1_models_queried_then_qwen3_6_27b_awq_served_name_present(vllm_base_url, vllm_api_key):
    # Arrange

    # Act
    with _get_models(vllm_base_url, vllm_api_key) as r:
        models = json.loads(r.read())

    # Assert
    served_ids = [m['id'] for m in models['data']]
    assert 'qwen3.6-27b-awq' in served_ids, f'served={served_ids}'


def test_when_chat_completion_sent_then_response_has_non_empty_content(vllm_base_url, vllm_api_key):
    # Arrange
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [{'role': 'user', 'content': 'Say hi.'}],
        'max_tokens': 16,
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
    with urllib.request.urlopen(req, timeout=60) as r:
        status = r.status
        data = json.loads(r.read())

    # Assert
    assert status == 200
    content = data['choices'][0]['message']['content']
    assert content, 'empty content'


@pytest.mark.live
def test_when_skill_tier1_prompt_sent_then_reply_completes_within_5_min(vllm_base_url, vllm_api_key):
    from pathlib import Path
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    skill = (repo / 'tasks/2048/SKILL_tier1.md').read_text()
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': [
            {'role': 'system', 'content': 'You are a reward-bench Tier 1 author. Read the task spec and respond with the final Python module inside a single fenced python code block. No prose outside the fence.'},
            {'role': 'user', 'content': skill},
        ],
        'max_tokens': 8192,  # cycle 99b: was 32768; ~73 tok/s vLLM throughput puts the full budget over the 5-min ceiling.
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
    with urllib.request.urlopen(req, timeout=300) as r:
        status = r.status
        data = json.loads(r.read())

    # Assert
    assert status == 200
    content = data['choices'][0]['message']['content']
    assert content, 'empty content'


def test_when_bench_provisions_inference_then_qwen3_6_27b_awq_serves_with_128k_context(vllm_api_key):
    from src.tier1.inference import ensure_serving
    # Arrange (handled by ensure_serving call)

    # Act
    base_url = ensure_serving()
    with _get_models(base_url, vllm_api_key) as r:
        status = r.status
        models = json.loads(r.read())

    # Assert
    assert status == 200
    ids = [m['id'] for m in models['data']]
    assert 'qwen3.6-27b-awq' in ids, f'served={ids}'
    matching = [m for m in models['data'] if m['id'] == 'qwen3.6-27b-awq'][0]
    assert matching['max_model_len'] >= 131072, f'max_model_len={matching["max_model_len"]}'



def test_when_ensure_serving_model_called_with_target_then_docker_run_invoked_with_target_params(monkeypatch):
    """Cycle 42: pin the docker run argv shape for model-swap provisioning."""
    from src.tier1 import inference as inf
    from src.reward_bench.entities.model_target import ModelTarget

    target = ModelTarget(
        id='devstral-small-2-24b',
        hf_path='Firworks/Devstral-Small-2-24B-Instruct-2512-nvfp4',
        served_name='devstral-small-2-24b',
        max_model_len=131072,
        tool_call_parser='mistral',
    )

    # Record every docker call; produce stateful responses simulating
    # "no container -> after run, container exists at 172.18.0.42".
    captured = []
    state = {'brought_up': False}
    class _Resp:
        def __init__(self, stdout='', returncode=0):
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = ''
    def fake_run(cmd, **kwargs):
        captured.append(list(cmd))
        # inspect IP: empty until container is "brought up".
        if cmd[:2] == ['docker', 'inspect']:
            return _Resp(stdout='172.18.0.42\n' if state['brought_up'] else '')
        # ps -a — empty (no container yet).
        if 'ps' in cmd:
            return _Resp(stdout='')
        # docker rm -f — no-op.
        if cmd[:3] == ['docker', 'rm', '-f']:
            return _Resp()
        # docker run — flip the flag.
        if cmd[:2] == ['docker', 'run']:
            state['brought_up'] = True
            return _Resp()
        return _Resp()
    monkeypatch.setattr(inf.subprocess, 'run', fake_run)

    # Mock urllib so /v1/models returns served_name in body immediately.
    class _MockResp:
        status = 200
        def __init__(self, body):
            self._body = body
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return self._body
    def fake_urlopen(req, timeout=5):
        return _MockResp(f'{{"data": [{{"id": "{target.served_name}"}}]}}'.encode())
    monkeypatch.setattr(inf.urllib.request, 'urlopen', fake_urlopen)

    monkeypatch.setenv('VLLM_API_KEY', 'stub')

    # Act
    url = inf.ensure_serving_model(target)

    # Assert: URL well-formed
    assert '172.18.0.42:8000' in url, f'unexpected URL: {url}'

    # Assert: docker run invoked with target params
    run_cmds = [c for c in captured if c[:2] == ['docker', 'run']]
    assert run_cmds, f'no docker run cmd captured; got {captured!r}'
    run_argv = run_cmds[0]
    joined = ' '.join(run_argv)
    assert target.hf_path in joined, f'hf_path missing from {joined}'
    assert f'--served-model-name {target.served_name}' in joined or (
        '--served-model-name' in run_argv and
        target.served_name in run_argv
    )
    assert f'--max-model-len {target.max_model_len}' in joined or (
        '--max-model-len' in run_argv and
        str(target.max_model_len) in run_argv
    )
    assert f'--tool-call-parser {target.tool_call_parser}' in joined or (
        '--tool-call-parser' in run_argv and
        target.tool_call_parser in run_argv
    )
