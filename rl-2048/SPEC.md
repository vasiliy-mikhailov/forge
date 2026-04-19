# rl-2048 — sandbox for RL / GRPO experiments

## Purpose
A Jupyter environment with a "heavy" ML stack (vLLM + unsloth +
transformers + bitsandbytes + flash-attn) for experiments with RL and
fine-tuning LLMs. The historical name is from the original task of tuning
a model to play 2048; today it's a general sandbox for any GRPO/SFT
experiments.

## Non-goals
- Not a production service. No serving, no batch inference.
- Experiment code is not stored in git — notebooks accumulate secrets,
  paths, and big outputs quickly.

## Architecture
One container `jupyter-rl-2048`, built from the local Dockerfile. GPU is
passed through via `RL_2048_GPU_UUID` (default: the Blackwell GPU; the
rtx5090 stays dedicated to kurpatov-wiki).

Volumes:
- `./notebooks → /workspace/notebooks` — the only place I write new
  experiments. Not in git.
- `${STORAGE_ROOT}/models → /workspace/models` — shared HuggingFace cache
  (shared with kurpatov-wiki).
- `${STORAGE_ROOT}/rl-2048/checkpoints → /workspace/checkpoints` —
  checkpoints.

Accessed externally via caddy (`JUPYTER_RL_2048_DOMAIN`) with basic auth.
Writes metrics to mlflow via https + basic auth (`MLFLOW_*` env vars).

## Data contracts
- Inputs: arbitrary HF datasets, models (loaded into `/workspace/models`).
- Outputs: checkpoints in `/workspace/checkpoints`, metrics/artifacts in
  mlflow.

No formal contract — this is a research environment, no backwards
compatibility between notebooks is guaranteed.

## Invariants
1. Uses exactly the GPU named by `RL_2048_GPU_UUID`. If that same UUID ends
   up in `KURPATOV_WIKI_GPU_UUID`, the second service will OOM.
2. Image rebuild is triggered by `make rl-2048-build` (from the forge
   root). After editing the Dockerfile:
   `make rl-2048-down && make rl-2048-build && make rl-2048`.
3. `shm_size: 16gb` — needed for some compile flows in torch/flash-attn,
   don't lower it.

## Status
Work-in-progress (sandbox). Dockerfile is periodically updated for new
versions of vllm / unsloth / transformers.

## Open questions
- Split a "stable" image (proven on my CU129 + Blackwell) from an
  "experimental" one with bleeding-edge versions. Needed eventually, not
  urgent.
- Integration with kurpatov-wiki: will LLM-based video summarization use
  this same stack or a separate image? Decide when we get to that task.
