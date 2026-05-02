# Service: Container runtime + GPU isolation

- **Component:** Docker + CUDA 13 + nvidia-container-toolkit. Image
  `kurpatov-wiki-bench:1.17.0-d8-cal` bakes openhands-sdk +
  sentence-transformers + e5-base + bench scripts under
  `/opt/forge/`.

## Quality dimensions and trajectories

- **Stability** — L1: works for steady-state, but `docker rm -f`
  on a CUDA-active container leaves an orphan kernel-side context
  (G1-H3: observed 2026-04-27 when killing a side-experiment
  container left the *other* GPU at 100 % util / 110 W draw with
  no userspace owner; per-GPU reset failed; orphan only cleared by
  full driver reload).
  L2: convention codified — always `docker stop` (SIGTERM + grace)
  before `docker rm -f` for CUDA containers.

## Cross-references

- [`../../phase-g-implementation-governance/policies/containers.md`](../../phase-g-implementation-governance/policies/containers.md)
  — the forge-wide containers-only execution rule.


## Motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: P3 (containers-only) requires a docker compose
  topology; the runtime spec lives here.
- **Goal**: Service operation (P3 enforced).
- **Outcome**: docker compose per Lab; one host (P4) muxed
  by Caddy per ADR 0007.
- **Measurement source**: audit-predicate: P3 (containers-only enforcement)
- **Capability realised**: Service operation.
- **Function**: Define-container-runtime-topology.
- **Element**: this file.
