FROM nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip python3-dev \
      ca-certificates curl git \
      ffmpeg libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

# uv from pypi (install.sh hangs inside some BuildKit builders).
RUN pip install --break-system-packages uv

RUN uv venv /opt/venv --python=3.12 --seed
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace

# PyTorch with CUDA 12.9 — explicit index-url, no --torch-backend magic
RUN uv pip install \
      --index-url https://download.pytorch.org/whl/cu129 \
      torch torchaudio torchcodec

# Transcription stack — from the default PyPI
RUN uv pip install \
      "ctranslate2>=4.6.0" \
      "faster-whisper>=1.1.1" \
      "pyannote.audio>=3.3.2" \
      soundfile av

RUN uv pip install jupyterlab ipywidgets tqdm watchdog

ENV HF_HOME=/workspace/models \
    HF_DATASETS_CACHE=/workspace/models \
    TORCHINDUCTOR_CACHE_DIR=/workspace/.inductor_cache

EXPOSE 8888

CMD ["bash", "-lc", "\
  jupyter lab \
    --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
    --ServerApp.token='' \
    --ServerApp.password='' \
    --notebook-dir='/workspace' \
"]
