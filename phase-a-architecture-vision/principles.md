# Principles

- **Single architect of record.** No committee, no formal review
  process beyond AGENTS.md conventions.
- **Capability trajectories.** Every capability has Level 1 (today)
  and Level 2 (next planned state). When L2 is reached, it becomes
  the new L1 and the prior L1 is deleted from docs; git is the
  archive. No `Withdrawn` / `Deprecated` / `Closed` status flags in
  the working tree.
- **Containers-only execution** (`phase-g-implementation-governance/policies/containers.md`).
- **Single-server deployment** on `mikhailov.tech` — all services
  share one host, one network, two GPUs.
