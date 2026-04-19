# rl-2048 — sandbox for RL / GRPO experiments

## Purpose
A Jupyter environment with a "heavy" ML stack (vLLM + unsloth +
transformers + bitsandbytes) for experiments with RL and fine-tuning
LLMs. The historical name is from the original task of tuning a model to
play 2048; today it's a general sandbox for any GRPO/SFT experiments.

## Non-goals
- Not a production service. No serving endpoint, no batch inference
  pipeline.
- No standalone helper scripts (`build.sh`, password hashers, etc.). The
  root `Makefile` drives everything: `make rl-2048-build`, `make
  rl-2048`, `make rl-2048-down`.

## Architecture
One container `jupyter-rl-2048`, built from the local Dockerfile. GPU is
passed through via `RL_2048_GPU_UUID` (default: the Blackwell RTX PRO
6000 Workstation; the rtx5090 stays dedicated to kurpatov-wiki).

Base image: `nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04`. Python 3.12
venv managed with `uv`. Key packages:

- `vllm` (installed first, with `--torch-backend=cu129`, which pulls the
  matching torch build).
- `unsloth==2026.1.4` + `unsloth_zoo==2026.1.4`, `bitsandbytes`.
- `transformers==4.57.3`.
- `jupyterlab`, `ipywidgets`, `mlflow` client.

Volumes:
- `./notebooks → /workspace/notebooks` — scratch space for experimental
  notebooks. Not in git.
- `${STORAGE_ROOT}/models → /workspace/models` — shared HuggingFace cache
  (shared with kurpatov-wiki).
- `${STORAGE_ROOT}/rl-2048/checkpoints → /workspace/checkpoints` —
  checkpoints.

Accessed externally via caddy (`JUPYTER_RL_2048_DOMAIN`) with basicauth —
Jupyter itself runs with no token / no password because Caddy handles
TLS + auth in front of it. Writes metrics to mlflow via https + basic
auth (`MLFLOW_TRACKING_URI`, `MLFLOW_TRACKING_USERNAME`,
`MLFLOW_TRACKING_PASSWORD`).

## Tracked notebook
`rl-2048/2048_gpt_oss_20b.ipynb` — the current GRPO experiment on
GPT-OSS-20B, whitelisted against the global `*.ipynb` ignore. Living
here at the rl-2048/ root (next to Dockerfile) marks it as a
source-of-truth artifact, not a throwaway. When iterating, copy it into
`./notebooks/` (which is the only bind-mount into jupyter), work there,
and promote back to the root with `cp notebooks/2048_gpt_oss_20b.ipynb
2048_gpt_oss_20b.ipynb` before committing.

All other notebooks (scratch, variants) stay in `./notebooks/` and are
git-ignored.

## Data contracts
- Inputs: arbitrary HF datasets, models (loaded into `/workspace/models`).
- Outputs: checkpoints in `/workspace/checkpoints`, metrics/artifacts in
  mlflow.

No formal contract — this is a research environment, no backwards
compatibility between notebook revisions is guaranteed.

## Invariants
1. Uses exactly the GPU named by `RL_2048_GPU_UUID`. If that same UUID
   ends up in `KURPATOV_WIKI_GPU_UUID`, the second service will OOM.
2. Image rebuild is triggered by `make rl-2048-build` (from the forge
   root). After editing the Dockerfile:
   `make rl-2048-down && make rl-2048-build && make rl-2048`.
3. `shm_size: 16gb` — needed for some compile flows in torch, don't
   lower it.
4. Only one `.ipynb` is tracked in git
   (`rl-2048/2048_gpt_oss_20b.ipynb`), whitelisted against the global
   `*.ipynb` ignore. Everything else in `./notebooks/` is scratch.

## Status
Work-in-progress (sandbox). Dockerfile is periodically updated for new
versions of vllm / unsloth / transformers.

## Open questions
- Split a "stable" image (proven on my CU129 + Blackwell) from an
  "experimental" one with bleeding-edge versions. Needed eventually, not
  urgent.
- Integration with kurpatov-wiki: will LLM-based video summarization use
  this same stack or a separate image? Decide when we get to that task.
- The tracked notebook has outputs baked in — worth running `nbstripout`
  before committing updates, so diffs stay readable.
