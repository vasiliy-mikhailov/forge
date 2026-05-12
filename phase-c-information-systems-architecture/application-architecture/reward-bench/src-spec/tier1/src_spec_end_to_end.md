# Tier 1 end-to-end (real model → real harness, layered)

## Purpose

Prove that the live `qwen3.6-27b-awq`, given the `SKILL_tier1.md` task
spec, produces a Tier 1 submission the harness can load and play.

Per the [phase-g/tsdd.md](../../../../../phase-g-implementation-governance/tsdd.md)
decomposition rule, this is broken into ten independent tests, each
pinning one observable layer.

## Layers

| Id   | Layer behavior                                                                                |
|------|-----------------------------------------------------------------------------------------------|
| L1.1 | vLLM serves: `GET /v1/models` returns 200.                                                    |
| L1.2 | Correct model loaded: served_name `qwen3.6-27b-awq` present.                                  |
| L2.1 | Chat completion works: `POST /v1/chat/completions` on a trivial prompt returns 200 + content. |
| L3.1 | Tier-1 prompt (SKILL_tier1.md content) returns within 5 min at `max_tokens=32768`.            |
| L3.2 | Reply contains one fenced Python block.                                                       |
| L4.1 | Extracted source has no `SyntaxError`.                                                        |
| L5.1 | Loaded module exposes `class Solver`.                                                         |
| L5.2 | `Solver()` instantiates and exposes a callable `move` attribute.                              |
| L6.1 | `solver.move(starting_board)` returns one of `{W, A, S, D}`.                                  |
| L6.2 | Full game with `seed=42` terminates and produces a non-negative score.                        |

## Shared expensive setup

Layers L3.2 through L6.2 all consume the same model reply. They share
a session-scoped pytest fixture that performs the L3.1 model call once
per test session. The fixture re-runs every fresh pytest invocation
so the model output is never frozen on disk.
