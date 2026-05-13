# `src/reward_bench/entities/attempt_meta.py`

`AttemptMeta` is a frozen dataclass — the identity + provenance
record for one bench attempt. Mirrors the pydantic schema in
[`SPEC.md`](../../../../SPEC.md#schemas-pydantic-v2) (`meta.json`
file).

## Fields

| Field               | Type       | Meaning                                                            |
| ------------------- | ---------- | ------------------------------------------------------------------ |
| `run_id`            | `str`      | E.g. `2026-05-04-180423-qwen36-27b-fp8-tier1`.                     |
| `model_id`          | `str`      | Matches a `ModelTarget.id`.                                        |
| `served_model_name` | `str`      | What vLLM advertises on `/v1/models`.                              |
| `task_id`           | `TaskId`   | Currently `Literal['2048']`; expand as tasks land.                 |
| `tier`              | `int`      | 1..4. Matches a `TierSpec.tier`.                                   |
| `started_at`        | `datetime` | When the attempt began.                                            |
| `image_digest`      | `str`      | sha256 of sandbox image (reproducibility).                         |
| `forge_commit`      | `str`      | forge git rev at attempt time.                                     |

## Properties

Frozen, no methods, pure data. Equality by field value.
