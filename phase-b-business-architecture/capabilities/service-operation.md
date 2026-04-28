# Capability: Service Operation (production framework)

One of forge's four business capabilities (Phase B). Service Operation
is the ability to run forge's production-framework services
*reliably, cheaply, and fast enough that R&D output throughput is
not bottlenecked on infrastructure*. It is forge's "keep the lights
on" capability.

This capability covers infrastructure as a *behaviour* (services
that run, deliver, recover); the concrete components and tech stack
that realise it live in Phase D Technology Architecture.

## Quality dimensions

Each dimension has a measurable metric, a current value, and a
target. Every capability advance moves at least one of them.

| Dimension                    | Metric                                                         | Current (Level 1)                                                                 | Next target (Level 2)                                              |
|------------------------------|----------------------------------------------------------------|-----------------------------------------------------------------------------------|--------------------------------------------------------------------|
| **Stability**                | Mean-time-between-crashes on sustained 27B inference           | ≥ 169 min (one full module-005 pilot v5, no crash) at 400 W cap with persistence  | Stable across 200-source runs (≥ 24 h continuous)                  |
| **Throughput** — decode      | tok/s decode batch=1                                           | ~47 tok/s (Qwen3.6-27B-FP8 on Blackwell at 400 W)                                 | ≥ 100 tok/s (G2 hypothesis below)                                  |
| **Throughput** — prefill     | tok/s prefill batch=1                                          | ~6,300 tok/s honest (raw); ~30 K tok/s with vLLM prefix-cache hit                 | (currently not the bottleneck — defer)                              |
| **Cost-per-output-token**    | GPU-Wh per 1 K output tokens                                   | 400 W ÷ (47 tok/s × 60) ≈ 142 Wh / 1 K output tok                                 | ≤ 60 Wh / 1 K output tok (function of throughput improvement)       |
| **Latency** (per-LLM-call)   | wall-clock seconds for a typical bench sub-agent call          | ~5-30 s (depends on output length)                                                 | (not on the active trajectory)                                      |

The first three are the active dimensions today. *Stability* was
just advanced from "~50 % crash rate within 2.5 h" to its current
Level 1 by experiment **G1** (closed 2026-04-27 — 400 W power cap +
persistence mode; see
`phase-f-migration-planning/experiments/G1-blackwell-stability.md`).
*Throughput* is the next active trajectory.

## Realised by

`wiki-compiler` lab is the primary realiser:

- vLLM 0.19.1 (cu130) serving the active LLM.
- caddy 2 reverse proxy + TLS termination at
  `inference.mikhailov.tech`.
- Persistence-aware GPU power management
  (`/etc/systemd/system/nvidia-power-limit.service` — 400 W cap on
  the Blackwell with `-pm 1`).

`wiki-ingest` realises the *transcription service* version of this
capability (faster-whisper). Different stack, same capability
shape.

## Active trajectory: G2 — faster inference via MoE

**Hypothesis (IF–THEN–BECAUSE):**

> **IF** we swap the served model from Qwen3.6-27B-FP8 (dense, all
> 27 B params active per decode step) to Qwen3.6-35B-A3B (Mixture-of-
> Experts: 35 B total params, only ~3 B active per token via expert
> routing), **THEN** decode throughput on the Blackwell will roughly
> 4-8× (target ≥ 100 tok/s, possibly 200+), pilot wall time on a
> 7-source module will drop from ~169 min to ~50-90 min, and
> architect-velocity per pilot improves proportionally,
> **BECAUSE** decode on a single Blackwell is memory-bandwidth-bound
> (current 47 tok/s ≈ 80 % of the theoretical ceiling 1.6 TB/s ÷
> 27 GB FP8 weights ≈ 60 tok/s). MoE inference reads only the active
> experts per token (~3 GB per step instead of 27 GB), raising the
> ceiling roughly an order of magnitude. Quality on the
> wiki-compilation task should be at-or-near the dense 27 B baseline
> (Qwen team's own benchmarks for the A3B variant), but that's part
> of what the experiment validates.

**Falsification criteria:**

1. Decode throughput < 80 tok/s on the same Blackwell (under 400 W
   cap) — MoE benefit didn't materialise on this hardware.
2. Pilot v6 metrics on module 005 (REPEATED, claims_total,
   structural compliance) regress > 20 % vs pilot v5 — quality cost
   of MoE switch > the throughput benefit. (i.e. MoE is faster but
   gives noticeably worse output.)

Either falsification means: revert to Qwen3.6-27B-FP8.

**Sequenced steps** in
`phase-f-migration-planning/experiments/G2-MoE-faster-inference.md`.

## Other open hypotheses (not yet active)

- **Cache-reuse across sub-agent delegations** (would advance prefill
  cost): vLLM 0.19's prefix cache already helps when the same system
  prompt is reused; an openhands-side change to keep KV cache warm
  across same-Conversation sub-agent calls would compound this.
- **Smaller dense model** if MoE fails: drop to Qwen2.5-14B or 7B
  for production runs at the cost of some quality.
- **Batched bench**: if multiple labs queued LLM work, vLLM batching
  would amortise prefill across requests. Not relevant at single-
  pilot scale today.

## Reference

- Phase D Technology Architecture: `forge/AGENTS.md` § Phase D —
  the LLM inference service entry lists current components +
  versions.
- Phase H trajectory rule: when Level 2 is reached, it becomes the
  new Level 1; the prior Level 1 description is deleted from this
  file. Git history keeps every prior level.
- Active experiment specs: `phase-f-migration-planning/experiments/`.
