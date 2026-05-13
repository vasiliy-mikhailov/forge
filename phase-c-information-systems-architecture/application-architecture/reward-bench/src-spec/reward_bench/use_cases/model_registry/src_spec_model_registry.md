# `src/reward_bench/use_cases/model_registry.py`

`MODEL_REGISTRY` is a tuple of `ModelTarget` value objects — the
complete catalogue of candidate models the bench evaluates. It is the
Python-side mirror of the YAML registry at
[`wiki-compiler/configs/models.yml`](../../../../../wiki-compiler/configs/models.yml).

## Contents

Each entry in `MODEL_REGISTRY` is one `ModelTarget`. The registry
currently lists **21 models** across four tiers:

| Tier | Class                                | Count |
| ---- | ------------------------------------ | ----- |
| A    | dense 24-32B, single Blackwell       | 13    |
| B    | dense 49-72B, tight VRAM             | 4     |
| C    | 100B+ (AWQ-INT4 / NVFP4 / MoE)       | 4     |

Models marked `bench_skip: true` in `models.yml` are intentionally
excluded:

- `qwen3.6-27b-awq-int4-community` (legacy refuted crash baseline)
- `qwen3.6-35b-a3b-fp8` (MoE out of scope per 2026-05-05 direction)

## Invariants

- Every entry has every `ModelTarget` field populated (no defaults,
  no `None`).
- `id` is unique across the registry.
- `served_name` equals `id` (registry convention; the YAML has one
  legacy exception which is in the skip list).
- `tool_call_parser` is one of: `qwen3_xml`, `mistral`, `gemma4`,
  `llama3_json`, `hermes`, `openai`.

## Use

The bench orchestrator iterates `MODEL_REGISTRY` to schedule
campaigns; a tier module receives one `ModelTarget` at a time via the
orchestrator and never reaches into the registry itself.

## Source of truth

When `models.yml` grows or shrinks, this tuple must follow. The
architectural drift between YAML and Python is pinned by a separate
test (TODO: cycle to add a yaml-vs-tuple consistency test once a
YAML loader use case lands).
