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

## P6 — Completeness over availability for compiled artifacts

For pipelines that produce a compiled artifact users will read or query
as if it were authoritative — the wiki, a concept index, an evaluation
report — **silent data loss is worse than failure**. A pipeline that
crashes on source 9 of 44 is recoverable: the operator sees the failure,
fixes the bug, reruns. A pipeline that silently skips source 9 and ships
a 43-source wiki labelled "44 sources processed" is unrecoverable in
practice — every downstream reader treats the result as complete, and
the gap becomes invisible.

Concrete sub-rules:

- **No silent skipping.** If a source fails verification, the pipeline
  either (a) crashes with a clear error and exits non-zero, or (b) under
  an explicit `continue-on-fail` policy, writes a skipped-sources
  manifest, exits non-zero, and emits a "WIKI INCOMPLETE — N sources
  skipped" banner in the run report. Continue-on-fail is for *partial
  progress on long pilots*, not for *covering up bugs*.
- **The default is fail-fast.** `continue-on-fail` is opt-in via env
  var, never the default. The operator must consciously accept the
  trade-off ("I want partial progress; I will reconcile skips by hand").
- **Skip ≠ success.** Pilot summaries report `verified=ok`,
  `verified=fail`, and `skipped` as three distinct counts. Aggregate
  quality metrics are computed only over `verified=ok`; the `skipped`
  count is the correctness debt.
- **Test fidelity matters here too.** A green synth test that doesn't
  reproduce a production verify-fail is itself silent data loss at the
  test layer — it claims the system is correct when it isn't. ADR 0010
  exists for this reason.

This principle was learned the hard way during K1 (2026-04-29): the
continue-on-fail policy turned a real wiki-correctness bug (verify_source
falsely reporting "fail" on healthy files) into a 6-source silent gap in
the wiki for module 001. The bug was not the verify-fail itself — that
is a recoverable state. The bug was the *policy that hid the failures
behind a "pilot completed" banner*. Skipping a lecture is worse than
crashing on it: a crashed pilot gets fixed; a skipped lecture quietly
poisons every search, every cross-reference, every "completeness" claim
the wiki makes.

The fix lives in
[`phase-c-…/wiki-bench/orchestrator/run-d8-pilot.py`](../phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator/run-d8-pilot.py)
(skipped-sources manifest, non-zero exit, INCOMPLETE banner) and the
matching
[`docs/adr/0012-no-silent-skip-for-wiki-sources.md`](../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0012-no-silent-skip-for-wiki-sources.md).

The P6 sub-rule that surfaced first in production is captured in
[forge ADR 0011 — NFC/NFD cross-platform paths](../phase-g-implementation-governance/adr/0011-nfc-nfd-cross-platform-paths.md):
the K1 silent skip was a function of macOS-NFD filenames meeting an
LLM tokenizer that emits NFC, with no normalisation in between. P6
forbids the silent skip; ADR 0011 fixes the cross-platform hazard
that produced it.

## P7 — Universal motivation traceability

Every architecture element (regardless of TOGAF phase, ArchiMate
layer, or ArchiMate aspect) MUST cite a measurable motivation chain (OKRs)
(Driver → Goal → Outcome → Capability → Function → Role /
Component / Process) OR be transitively covered per
[ADR 0013 dec 9](adr/0013-md-as-source-code-tdd.md) with the
abstract / parent named explicitly.

Default = required. Opt-out = transitive carve-out with
documented rationale citing the abstract artifact whose chain it
inherits. Detail in
[ADR 0017](adr/0017-motivation-spans-all-layers.md).

**Why this is a load-bearing rule.** ArchiMate (§6) treats
**Motivation as an Aspect** that spans every Layer (Strategy,
Business, Application, Technology, Physical, Implementation &
Migration). Forge's pre-2026-05-02 enforcement was piecemeal:
P14 covers role files; P15 covers catalog rows; P17 covers test
cases; P18 + P19 cover Driver / Goal chain. New artifact types
(Phase D files, Phase G procedures, Python scripts, new ADRs)
silently lacked motivation traceability until the audit caught
them — at which point yet another retroactive predicate got
bolted on. P7 makes the default fail-closed: a new artifact
type without a chain (and without a transitive carve-out) is a
P24 FAIL on the next audit walk.

**Verification**. P24 in
[`../phase-h-architecture-change-management/audit-process.md`](../phase-h-architecture-change-management/audit-process.md)
walks every md under `phase-*/` and verifies the chain section
is present (or a transitive-coverage line is).

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
- A pipeline whose default behaviour is "skip the failing item and
  keep going" violates P6 — the default must be fail-fast, with
  continue-on-fail an explicit, manifest-producing opt-in.
- A new ADR / Phase D architecture file / Phase G procedure /
  experiment spec that lacks a `## Measurable motivation chain (OKRs)` section AND
  lacks a `Transitive coverage:` line citing its abstract
  violates P7 — P24 surfaces it as FAIL on the next audit walk.

## Why these seven

P1 and P4 reflect the lived constraints of a home-lab single-
architect setup; P2, P3, P5, P6 are *deliberate* choices that
could in principle be relaxed but have proven to be the load-bearing
rules that keep the working tree honest and the architect's hours
spent on capability advances rather than on rework. P7 (added
2026-05-02 per [ADR 0017](adr/0017-motivation-spans-all-layers.md))
is the meta-rule that prevents motivation traceability from
leaking out as new artifact types appear.

The principles are the answer to the question "what would I be
willing to throw away first?" — and the answer is: not these.


## Measurable motivation chain (OKRs)
Per P7 (the principle this file holds):

- **Driver**: forge needs explicit architecture principles to
  prevent decision drift across architect-sessions.
- **Goal**: Architect-velocity (principles are the meta-rule
  that keeps every per-phase decision consistent).
- **Outcome**: 7 Principles (P1..P7); each new architectural
  decision is checked against them.
- **Measurement source**: audit-predicate: P7 (universal motivation traceability; meta-principle file enumerating P1..P7)
- **Capability realised**: Architecture knowledge management.
- **Function**: Hold-the-7-load-bearing-principles.
- **Element**: this file.
