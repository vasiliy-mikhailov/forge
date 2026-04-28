# Architecture principles

The meta-rules every architecture decision in forge must obey.
These sit above any single phase — they constrain Phase A through
Phase H equally. New ADRs and trajectory steps that contradict one
of these principles are wrong by construction.

## P1 — Single architect of record

There is one decision-maker. No committee, no Architecture Board,
no formal review process beyond AGENTS.md conventions. Detail in
[`architecture-team.md`](architecture-team.md).

## P2 — Capability trajectories

Every capability has **Level 1** (today) and **Level 2** (next
planned state). When Level 2 is reached, it becomes the new Level
1; the prior Level 1 description is deleted from docs. Git history
keeps every prior level — that is the archive. No `Withdrawn`,
`Deprecated`, or `Closed` status flags in the working tree;
presence of text means current, absence means git history. Detail
in [`architecture-method.md`](architecture-method.md).

## P3 — Containers-only execution

Every executable artefact (orchestrators, helper scripts,
evaluators, retrieval indexes) runs inside Docker. No host-Python
runs in production. No host-pip installs of new dependencies. The
forge contract is: every run is replayable from the artifact +
Dockerfile. Detail in
[`../phase-g-implementation-governance/policies/containers.md`](../phase-g-implementation-governance/policies/containers.md).

## P4 — Single-server deployment

All forge services share one host (`mikhailov.tech`), one network
(`proxy-net`), two GPUs (Blackwell + RTX 5090). The architecture
is single-machine until proven otherwise; we do not pre-engineer
for distribution. Multi-host deployment, if ever needed, is itself
a Phase F migration with its own ADR.

## How principles are applied

- A new technology service (Phase D) that requires host-Python
  installs violates P3 and is rejected at Phase F.
- A new capability (Phase B) without a Level 1 / Level 2 metric
  pair violates P2 and is rejected before any Phase F experiment.
- A change that would require a second architect to review every
  edit (e.g. mandatory PR review automation) violates P1 and is
  rejected at the governance layer (Phase G).
- A second host (a "GPU cluster" or "build server") violates P4
  unless the cost of staying on one host is shown to exceed the
  cost of distribution.

## Why these four

P1 and P4 reflect the lived constraints of a home-lab single-
architect setup; P2 and P3 are *deliberate* choices that could in
principle be relaxed but have proven to be the load-bearing rules
that keep the working tree honest.

The principles are the answer to the question "what would I be
willing to throw away first?" — and the answer is: not these.
