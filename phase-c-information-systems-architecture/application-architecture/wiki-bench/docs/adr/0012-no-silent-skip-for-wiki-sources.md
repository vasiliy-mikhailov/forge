# ADR 0012 — no silent skip for wiki sources

Status: Accepted
Date: 2026-04-29
Related: [P6](../../../../../phase-preliminary/architecture-principles.md), ADR 0010, ADR 0011

## Context

K1 pilot (2026-04-29) ran 44 sources with `D8_PILOT_FAIL_POLICY=continue` so
a single verify-fail wouldn't kill an overnight run. The policy worked as
written — the orchestrator did continue past failures. But what it produced
was strictly worse than a crash:

- Sources 9, 10, 11, 12, 13, 14 in module 001 verify-failed inside the same
  run.
- The orchestrator skipped them and kept going.
- Sources 8, 15, 16, 17 verified ok.
- The pilot summary reported "10 sources processed" without distinguishing
  ok from skipped.

A reader of the resulting wiki has no way to know that 6 lectures from the
middle of module 001 are missing. Cross-references to those lectures from
later sources would resolve to nothing. Concept articles whose canonical
introduction was in one of the skipped lectures would appear orphaned. The
wiki *looks* complete, *labels itself* complete, but is silently 6/14
short on the densest module.

This is exactly the failure mode P6 ("Completeness over availability for
compiled artifacts") forbids.

## Decision

The orchestrator's source-loop policy is updated as follows.

**Default behaviour: fail-fast.** Any verify-fail aborts the run with
non-zero exit. The operator sees the failure immediately and fixes it
before the wiki is published.

**Opt-in continue-on-fail (`D8_PILOT_FAIL_POLICY=continue`).** When
explicitly set, the run continues past verify-fails BUT must:

1. Append every skipped source to a `skipped_sources.json` manifest in
   the workdir, with `{n, slug, module_subdir, stem, violations,
   wall_min, agent_events}`.
2. Exit non-zero at end of run if the manifest is non-empty. The
   exit code carries the count: `min(125, num_skipped)` so CI cannot
   confuse "completed clean" with "completed with skips".
3. Print a banner at end of run:
   ```
   ============================================================
   WIKI INCOMPLETE — N sources skipped (see skipped_sources.json)
   ============================================================
   ```
4. Distinguish three counts in the summary: `verified_ok`,
   `verified_fail_skipped`, `errored`. Aggregate metrics
   (claims_total, REPEATED, CF, etc.) are computed only over
   `verified_ok`. `verified_fail_skipped` is the correctness debt.
5. Refuse to run a downstream "publish wiki" step when the manifest
   is non-empty. The publishing pipeline reads the manifest and aborts
   with a clear "wiki has N missing sources, refusing to publish"
   message.

**Reconciliation contract.** A skipped-sources manifest is a TODO list,
not an excuse. Every entry must be either reprocessed (manifest
shrinks) or explicitly marked as "intentionally excluded" with a
reason recorded in the manifest itself. The wiki publish pipeline
treats both states as acceptable, but only after the operator has
made the call.

## Why this matters more than the verify-fail bug itself

The K1 verify-fail (whose root cause is still under investigation per
ADR 0011 + the e2e test layer) is a *recoverable* state. It can be
diagnosed, fixed, and the affected sources reprocessed. It only becomes
*irrecoverable* when the orchestrator buries it under a "completed
successfully" report.

In other words: the verify-fail is a bug. The continue-on-fail policy as
previously implemented turned a bug into a quality-killing architectural
defect. P6 + this ADR fix the architecture; the verify-fail bug remains
to be fixed, but it can no longer hide.

## Consequences

- Long-running overnight pilots with continue-on-fail still produce
  partial progress, but the operator knows exactly what's missing.
- CI integration becomes meaningful: a green pilot run is now a real
  signal of completeness, not a meaningless "the script didn't crash".
- Wiki users get a hard guarantee: if it's published, every input
  source either contributed or is explicitly listed as excluded. No
  invisible gaps.
- Cost: marginal — one manifest write per skip, one banner at end,
  and the wiki publish step gets a manifest check.

## Anti-patterns rejected

- **Logging the skip and moving on without surfacing it.** Logs in
  the bench container are not part of the wiki contract. Operators
  reading the wiki output do not read docker logs.
- **Counting skipped as success.** `total_processed: 10` when 6 of
  the 10 are skipped is a lie by aggregation. Three distinct counts,
  always.
- **Auto-retrying skipped sources at the end of the run.** Tempting,
  but it conflates two failure modes (transient vs. systematic) and
  makes the manifest non-deterministic. Reprocessing is a separate,
  explicit operator step.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain (OKRs) inherited from the lab's AGENTS.md.
