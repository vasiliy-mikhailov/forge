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

## P5 — Metric-driven action

Every action choice — what to fix, how to fix it, in what order,
with what tooling — is evaluated against the four
[Motivation-layer goals](../phase-a-architecture-vision/goals.md):

- **TTS** — does this action increase Theoretical Time Saved per
  product use, or only feel productive?
- **PTS** — does this action grow Practical Time Saved (= TTS ×
  users × engagement), or is the user count too small to matter?
- **EB** — does this action improve Economic Balance, or does it
  burn architect-hours / GPU-hours / storage with no compensating
  return?
- **Architect-velocity** — does this action *advance* a capability
  per architect-hour, or is it iteration on architect-mistakes?

If the answer to all four is "no" or "not measurably", the action
is baggage. If it improves one at the visible cost of regressing
another, the trade-off is named explicitly in the
[Phase F experiment spec](../phase-f-migration-planning/experiments/)
or the relevant ADR — not silently absorbed.

**Concrete sub-rule: prefer the cheap experiment.** When a fix
needs validation, the canonical question is "what is the cheapest
artifact that gives the same signal?" — synth fixture vs. full
pilot, microbench vs. production rerun, unit test vs. live
re-deploy. The cheap artifact wins almost every time at single-
architect scale, because architect-velocity is the binding goal
and re-running expensive things to validate guesses *is* the
opposite of architect-velocity.

This principle was *learned the hard way* during K1
(2026-04-29): four hours of hot-patching a 30-line `verify_source`
function in production K1 reruns, when a 30-second synth test
would have surfaced the race deterministically on the first
attempt. The fix is in
[`phase-c-…/wiki-bench/tests/synthetic/test_verify_source.py`](../phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/synthetic/test_verify_source.py)
and the matching
[`docs/adr/0011-verify-source-existence-and-stability-poll.md`](../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0011-verify-source-existence-and-stability-poll.md)
— but the principle that should have prevented the four hours of
loss is here.

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
- A "let me just hot-patch and rerun" loop on a 25-min-per-run
  pilot violates P5 — the cheap path is a synth test that
  reproduces the bug on the architect's host in seconds. The
  loop is rejected at proposal time; the test is built first.

## Why these five

P1 and P4 reflect the lived constraints of a home-lab single-
architect setup; P2, P3, and P5 are *deliberate* choices that could in
principle be relaxed but have proven to be the load-bearing rules
that keep the working tree honest and the architect's hours
spent on capability advances rather than on rework.

The principles are the answer to the question "what would I be
willing to throw away first?" — and the answer is: not these.
