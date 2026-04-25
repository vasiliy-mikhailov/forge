FROM nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip python3-dev \
    ca-certificates curl git build-essential ninja-build pkg-config \
    openssl \
 && rm -rf /var/lib/apt/lists/*

# uv from pypi (install.sh hangs inside some BuildKit builders).
RUN pip install --break-system-packages uv

# venv
RUN uv venv /opt/venv --python=3.12 --seed
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace

# 1) Install vLLM first (selects torch/cu129)
RUN uv pip install -U vllm --torch-backend=cu129

# 2) flash-attn prerequisites + install (after torch exists)
RUN uv pip install psutil

# 3) Unsloth stack (avoid duplicating bitsandbytes)
RUN uv pip install "unsloth==2026.1.4" "unsloth_zoo==2026.1.4" bitsandbytes
RUN uv pip install "transformers==4.57.3"

# Jupyter
RUN uv pip install jupyterlab ipywidgets mlflow

# Caches
ENV HF_HOME=/workspace/models \
    TRANSFORMERS_CACHE=/workspace/models \
    HF_DATASETS_CACHE=/workspace/models \
    VLLM_CACHE_DIR=/workspace/.vllm_cache \
    TORCHINDUCTOR_CACHE_DIR=/workspace/.inductor_cache \
    TRITON_CACHE_DIR=/workspace/.triton_cache

EXPOSE 8888

# Run Jupyter without token/cert because Caddy provides HTTPS + BasicAuth
CMD ["bash", "-lc", "\
  jupyter lab \
    --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
    --ServerApp.token='' \
    --ServerApp.password='' \
    --notebook-dir='/workspace/notebooks' \
"]
