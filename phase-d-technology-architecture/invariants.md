# Forge-wide technology invariants

These apply to **every** technology service in Phase D, regardless of
which lab provides it.

- **Single-server deployment** on `mikhailov.tech`. All services
  share one host, one network, two GPUs.
- **Containers-only execution** — every executable artifact runs
  inside Docker. Source of truth:
  [`../phase-g-implementation-governance/policies/containers.md`](../phase-g-implementation-governance/policies/containers.md).
- **Persistence-aware GPU power management** — the Blackwell runs
  at a 400 W cap with `nvidia-smi -pm 1` (persistence-mode) via
  `/etc/systemd/system/nvidia-power-limit.service`. This is the
  binding fix for the UVM-crash failure mode (closed in
  `../phase-f-migration-planning/experiments/G1-blackwell-stability.md`).

Cross-cutting tech-quality dimensions (analogous to TTS/PTS/EB at
the Motivation layer): **throughput**, **latency**, **stability**
(mean-time-to-crash), **cost-per-output-token**. These feed
Architect-velocity and EB; they do not directly move TTS.

Trajectories (Level 1 / Level 2) attach to **service quality
dimensions**, not to components. Replacing a component (e.g.
vLLM 0.19.1 → 0.20) is just the next step on the same trajectory;
"Was vLLM 0.19.1" annotations do not stay in the working tree —
git remembers.


## Measurable motivation chain (OKRs)
Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: P3 + P4 + ADR 0007 imply invariants that any
  Phase D change must preserve (single host, containers-only,
  Caddy mux mutex, etc.).
- **Goal**: Service operation.
- **Outcome**: invariants enumerated; any new Lab proposal
  must show how it preserves them.
- **Measurement source**: audit-predicate: P3 + P4 (Phase D invariants = the principles the audit walks)
- **Capability realised**: Service operation + Architecture
  knowledge management.
- **Function**: Hold-Phase-D-invariants.
- **Element**: this file.
