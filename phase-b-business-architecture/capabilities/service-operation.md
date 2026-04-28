# Capability: Service Operation (production framework)

One of forge's four business capabilities (Phase B). Service
Operation is the ability to run forge's production-framework
services *reliably, cheaply, and fast enough that R&D output
throughput is not bottlenecked on infrastructure*. It is forge's
"keep the lights on" capability.

This capability covers infrastructure as a *behaviour* (services
that run, deliver, recover); the concrete components and tech
stack that realise it live in Phase D Technology Architecture.

## Quality dimensions

Each dimension has a measurable metric, a current value, and a
target. Every capability advance moves at least one of them.

| Dimension                    | Metric                                                         | Current (Level 1)                                                                 | Next target (Level 2)                                              |
|------------------------------|----------------------------------------------------------------|-----------------------------------------------------------------------------------|--------------------------------------------------------------------|
| **Stability**                | Mean-time-between-crashes on sustained 27B inference           | ≥ 169 min (one full module-005 pilot v5, no crash) at 400 W cap with persistence  | Stable across 200-source runs (≥ 24 h continuous)                  |
| **Throughput** — decode      | tok/s decode batch=1                                           | ~47 tok/s (Qwen3.6-27B-FP8 on Blackwell at 400 W)                                 | ≥ 100 tok/s decode at the pilot level (gated on the contract sub-trajectories — see Phase D) |
| **Throughput** — prefill     | tok/s prefill batch=1                                          | ~6,300 tok/s honest (raw); ~30 K tok/s with vLLM prefix-cache hit                 | (not the bottleneck — defer)                                       |
| **Cost-per-output-token**    | GPU-Wh per 1 K output tokens                                   | 400 W ÷ (47 tok/s × 60) ≈ 142 Wh / 1 K output tok                                 | ≤ 60 Wh / 1 K output tok (function of throughput improvement)       |
| **Latency** (per-LLM-call)   | wall-clock seconds for a typical bench sub-agent call          | ~5-30 s (depends on output length)                                                 | (not on the active trajectory)                                      |

The throughput dimension is the active trajectory. Direct
component swaps at the LLM layer (G2 MoE, G3 dense Gemma) have
been twice-falsified — pilot wall is dominated by per-claim
overhead and contract-enforcement gaps, not decode rate. The
pilot-level throughput target therefore decomposes into a chain
of Phase D sub-trajectories before it can be reached.

## Realised by

`wiki-compiler` lab is the primary realiser:

- vLLM 0.19.1 (cu130) serving the active LLM (Qwen3.6-27B-FP8
  today).
- caddy 2 reverse proxy + TLS termination at
  `inference.mikhailov.tech`.
- Persistence-aware GPU power management
  (`/etc/systemd/system/nvidia-power-limit.service` — 400 W cap
  on the Blackwell with `-pm 1`).

`wiki-ingest` realises the *transcription service* version of
this capability (faster-whisper). Different stack, same
capability shape.

## Decomposition into Phase D sub-trajectories

The pilot-level throughput target rolls up four Phase D
quality-dim trajectories. Each is its own row in the
[`phase-requirements-management/catalog.md`](../../phase-requirements-management/catalog.md):

- **R-D-contract-prewrite** (agent orchestration / contract
  enforcement). Source-author / curator must confirm a concept
  file exists before declaring `concepts_touched`.
- **R-D-contract-xreflint** (quality grading / cross-ref
  linting). Run `bench_grade.py --check-xrefs-only` after each
  source's commit; fail-fast on broken cross-refs so the agent
  retries with feedback.
- **R-D-retrieval-cost** (vector retrieval / per-call cost).
  Daemonize `embed_helpers.py` so the e5-base model loads once
  per pilot, not once per claim.
- **R-D-orchestration-kvcache** (agent orchestration / KV-cache
  reuse). Reuse vLLM prefix cache across same-Conversation
  sub-agent calls.

Sequenced execution lives in
[`../../phase-f-migration-planning/migration-plan.md`](../../phase-f-migration-planning/migration-plan.md).
The next LLM-component swap experiment is gated on the first
three landing — see
[`../../phase-e-opportunities-and-solutions/roadmap.md`](../../phase-e-opportunities-and-solutions/roadmap.md).

## Reference

- Phase D Technology Architecture:
  [`../../phase-d-technology-architecture/services/llm-inference.md`](../../phase-d-technology-architecture/services/llm-inference.md)
  — current components + versions.
- Phase H trajectory rule: see
  [`../../phase-preliminary/architecture-method.md`](../../phase-preliminary/architecture-method.md).
- Active experiment specs:
  [`../../phase-f-migration-planning/experiments/`](../../phase-f-migration-planning/experiments/).
