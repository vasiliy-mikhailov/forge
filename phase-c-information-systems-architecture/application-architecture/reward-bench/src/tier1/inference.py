"""Tier 1 inference provisioning. See src-spec/tier1/src_spec_when_bench_provisions_inference_*.md."""
import os
import subprocess
import time
import urllib.request

from src.reward_bench.entities.model_target import ModelTarget


CONTAINER = "reward-bench-vllm"
NETWORK = "proxy-net"
IMAGE = "vllm/vllm-openai:v0.20.0-cu130-ubuntu2404"
HF_PATH = "cyankiwi/Qwen3.6-27B-AWQ-INT4"
SERVED_NAME = "qwen3.6-27b-awq"
MAX_MODEL_LEN = 131072

_HEALTH_TIMEOUT_S = 360
_HEALTH_POLL_S = 10


def _inspect_ip():
    fmt = '{{(index .NetworkSettings.Networks "' + NETWORK + '").IPAddress}}'
    out = subprocess.run(
        ["docker", "inspect", CONTAINER, "--format", fmt],
        capture_output=True, text=True,
    )
    return out.stdout.strip() if out.returncode == 0 else ""


def _exists():
    out = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name=^{CONTAINER}$",
         "--format", "{{.Names}}"],
        capture_output=True, text=True,
    )
    return CONTAINER in out.stdout.split()


def _healthy(api_key):
    ip = _inspect_ip()
    if not ip:
        return None
    try:
        req = urllib.request.Request(
            f"http://{ip}:8000/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status != 200:
                return None
            body = r.read()
            if SERVED_NAME.encode() in body:
                return f"http://{ip}:8000"
    except Exception:
        return None
    return None


def _remove():
    subprocess.run(["docker", "rm", "-f", CONTAINER],
                   capture_output=True, text=True)


def _bring_up(api_key):
    gpu_uuid = os.environ.get("GPU_BLACKWELL_UUID", "")
    hf_token = os.environ.get("HF_TOKEN", "")
    cmd = [
        "docker", "run", "-d",
        "--name", CONTAINER,
        "--network", NETWORK,
        "--runtime", "nvidia",
        "-e", f"NVIDIA_VISIBLE_DEVICES={gpu_uuid}",
        "-e", "NVIDIA_DRIVER_CAPABILITIES=compute,utility",
        "-e", f"HUGGING_FACE_HUB_TOKEN={hf_token}",
        "--shm-size=16gb", "--ipc=host",
        "-v", "/mnt/steam/forge/shared/models:/root/.cache/huggingface",
        "-v", "/mnt/fire/forge/shared/models/hub:/mnt/fire/forge/shared/models/hub",
        IMAGE,
        "--model", HF_PATH,
        "--served-model-name", SERVED_NAME,
        "--max-model-len", str(MAX_MODEL_LEN),
        "--max-num-batched-tokens", "4096",
        "--max-num-seqs", "128",
        "--kv-cache-dtype", "fp8",
        "--gpu-memory-utilization", "0.85",
        "--enable-prefix-caching",
        "--enable-auto-tool-choice",
        "--tool-call-parser", "qwen3_coder",
        "--trust-remote-code",
        "--host", "0.0.0.0", "--port", "8000",
        "--api-key", api_key,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def ensure_serving():
    """Bring the lab vLLM container up if not already serving; return base URL."""
    api_key = os.environ["VLLM_API_KEY"]
    url = _healthy(api_key)
    if url is not None:
        return url
    if _exists():
        _remove()
    _bring_up(api_key)
    deadline = time.monotonic() + _HEALTH_TIMEOUT_S
    while time.monotonic() < deadline:
        url = _healthy(api_key)
        if url is not None:
            return url
        time.sleep(_HEALTH_POLL_S)
    raise TimeoutError(
        f"reward-bench-vllm did not become healthy within {_HEALTH_TIMEOUT_S} s"
    )


def _healthy_for_target(target):
    """Cycle 42: like _healthy but verifies the container serves
    `target.served_name` (not the hardcoded SERVED_NAME)."""
    ip = _inspect_ip()
    if not ip:
        return None
    api_key = os.environ["VLLM_API_KEY"]
    try:
        req = urllib.request.Request(
            f"http://{ip}:8000/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status != 200:
                return None
            body = r.read()
            if target.served_name.encode() in body:
                return f"http://{ip}:8000"
    except Exception:
        return None
    return None


def _bring_up_target(target, api_key):
    """Cycle 42: like _bring_up but parameterised by ModelTarget."""
    gpu_uuid = os.environ.get("GPU_BLACKWELL_UUID", "")
    hf_token = os.environ.get("HF_TOKEN", "")
    cmd = [
        "docker", "run", "-d",
        "--name", CONTAINER,
        "--network", NETWORK,
        "--runtime", "nvidia",
        "-e", f"NVIDIA_VISIBLE_DEVICES={gpu_uuid}",
        "-e", "NVIDIA_DRIVER_CAPABILITIES=compute,utility",
        "-e", f"HUGGING_FACE_HUB_TOKEN={hf_token}",
        "--shm-size=16gb", "--ipc=host",
        "-v", "/mnt/steam/forge/shared/models:/root/.cache/huggingface",
        "-v", "/mnt/fire/forge/shared/models/hub:/mnt/fire/forge/shared/models/hub",
        IMAGE,
        "--model", target.hf_path,
        "--served-model-name", target.served_name,
        "--max-model-len", str(target.max_model_len),
        "--max-num-batched-tokens", "4096",
        "--max-num-seqs", "128",
        "--kv-cache-dtype", "fp8",
        "--gpu-memory-utilization", "0.85",
        "--enable-prefix-caching",
        "--enable-auto-tool-choice",
        "--tool-call-parser", target.tool_call_parser,
        "--trust-remote-code",
        "--host", "0.0.0.0", "--port", "8000",
        "--api-key", api_key,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def ensure_serving_model(target: ModelTarget):
    """Cycle 42: (re)provision reward-bench-vllm to serve `target`.

    1. If container already serves target.served_name and is healthy,
       return its URL — no swap.
    2. Otherwise remove any existing container and start a new one
       with target's hf_path, served_name, max_model_len, parser.
    3. Wait up to _HEALTH_TIMEOUT_S for /v1/models to advertise the
       served_name.
    """
    api_key = os.environ["VLLM_API_KEY"]
    url = _healthy_for_target(target)
    if url is not None:
        return url
    _remove()
    _bring_up_target(target, api_key)
    deadline = time.time() + _HEALTH_TIMEOUT_S
    while time.time() < deadline:
        url = _healthy_for_target(target)
        if url is not None:
            return url
        time.sleep(_HEALTH_POLL_S)
    raise TimeoutError(
        f"reward-bench-vllm did not become healthy serving {target.served_name} "
        f"within {_HEALTH_TIMEOUT_S} s"
    )
