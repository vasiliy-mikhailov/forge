# ADR 0021 — Quality goal added to motivation layer; measured by pre-production bug-catch share

## Status

Accepted (2026-05-02). Active.

## Motivation

Per [P7](../architecture-principles.md):

- **Driver**: audit-2026-05-01y's contribution-report surfaced 6 ADRs
  classified Live but with 0 inbound references — all P3-related quality
  decisions (test-env-matches-prod, rebuild-before-launch, monorepo,
  data-outside-git, single-decision-per-deploy, single-source-of-truth).
  They had nothing to anchor to in the motivation layer because **Quality
  was not a named Goal**. Same root cause as pre-P7: discipline enforced
  piecemeal (each ADR knew it was about quality; the layer didn't).
- **Goal**: Quality (this ADR's addition; named in goals.md alongside
  TTS / PTS / EB / Architect-velocity).
- **Outcome**: every quality-affecting artifact cites a Quality
  motivation chain; the Quality metric is computed; the soft-orphan
  ADR set has a real anchor; the next quality decision lands with the
  citation built-in.
- **Measurement source**: quality-ledger: pre_prod_share (this ADR
  bootstraps the metric; quality-report.py computes it; first walk
  shows the actual share at this commit).
- **Capability realised**: Architecture knowledge management
  ([`../../phase-b-business-architecture/capabilities/forge-level.md`](../../phase-b-business-architecture/capabilities/forge-level.md)).
- **Function**: Add-Quality-to-motivation-layer.

## Context

ArchiMate § 6.4.1 defines a Goal as "a high-level statement of intent,
direction, or desired end state." Forge's pre-this-ADR Goal catalog had
4 entries: TTS, PTS, EB, Architect-velocity. None of them is what the
P3-family decisions optimise for. They optimise for **fewer
production incidents at the cost of slightly more pre-deploy
discipline** — the standard quality engineering trade.

The contribution-report run (commit `1a99fbc`) made the gap visible:

| Artifact (0-inbound) | What it decides |
|---|---|
| `phase-c/adr/0002-data-outside-git.md` | data not in git → fewer corruption incidents |
| `phase-d/adr/0005-inference-subsystem.md` | single inference subsystem → fewer cross-stack incidents |
| `phase-d/adr/0008-model-registry-single-source-of-truth.md` | one registry → fewer model-version incidents |
| `phase-f/adr/0006-inference-deploy-session-2026-04-25.md` | deploy session log → quality assurance |
| `phase-g/adr/0010-test-environments-match-production.md` | test-env = prod → fewer "works in dev fails in prod" incidents |
| `phase-g/adr/0012-rebuild-image-before-every-launch.md` | rebuild every launch → fewer stale-image incidents |
| `phase-preliminary/adr/0001-monorepo-flat-structure.md` | single repo → fewer cross-repo-skew incidents |

These ADRs all share a shape: a discipline that traded a small
pre-deploy cost for a large incident-rate reduction. They were
indistinguishable from "Live but underused" without a Quality Goal to
trace them to.

## Decision

### 1. Add Quality to phase-a/goals.md

A 5th top-level Goal:

> **Quality.** `pre_prod_share = pre_prod_catches / (pre_prod_catches +
> incidents)`, rolling 30-day window.

Per ArchiMate § 6.4.2, this is a Goal that has a measurable Outcome
(the `pre_prod_share` ratio) and an explicit metric.

### 2. Two ledgers — one explicit, one implicit

- **Incidents (explicit)** —
  [`phase-g-implementation-governance/postmortems.md`](../../phase-g-implementation-governance/postmortems.md).
  Append-only narrative ledger; each entry is a `***`-separated story
  ending in a `*Taken: ...*` line that points at the ADR / test /
  policy that prevents the recurrence. Format rules in the file's
  "How to write an entry" section.
- **Pre-prod catches (implicit)** — every `Findings — verdict FAIL`
  or `Findings — verdict WARN` entry under
  [`phase-h-architecture-change-management/audit-*.md`](../../phase-h-architecture-change-management/)
  is one pre-prod catch. The audit cadence (~24 walks since 2026-04-30)
  IS the pre-prod gate.

The split mirrors the standard "what shipped that hurt" vs "what got
caught before shipping" measurement model.

### 3. New citation type for ADR 0019

ADR 0019 § Decision 1's citation table gains an 11th row:

| `quality-ledger: <metric>` | Reads incident count from postmortems.md `***`-entries + pre-prod-catch count from audit FAIL/WARN findings | `quality-report.py` output |

Where `<metric>` is one of:
- `pre_prod_share` — the share, rolling 30-day.
- `incident_count` — raw incidents, rolling 30-day.

Used by quality-affecting artifacts (the 6 ADRs above + future P3-family
decisions + postmortems.md itself).

### 4. New audit predicate P28 — quality-affecting decisions cite Quality goal

Add **P28** to `audit-process.md`:

> **P28 — Quality-affecting decisions cite Quality goal.** An ADR or
> artifact whose Outcome involves "fewer production failures of class X",
> "match prod env in dev", "discipline catches a class of bugs", "rebuild
> / refresh before launch", "single source of truth", or any related
> reduction-of-incident-class motivation MUST cite `quality-ledger:` in
> its `**Measurement source**:` line. Walks via:
> `python3 scripts/test-runners/quality-report.py --predicate P28`.

P28 backfilled in the same commit per the predicate-+-sweep-+-same-commit
pattern from ADR 0017 / 0019.

### 5. Tooling — quality-report.py

`scripts/test-runners/quality-report.py`:
- Walks `phase-h-architecture-change-management/audit-*.md` for FAIL +
  WARN findings; counts each as one pre-prod catch.
- Walks `phase-g-implementation-governance/postmortems.md` for
  `***`-separated entries; counts each as one incident.
- Filters by 30-day rolling window (configurable).
- Emits `pre_prod_share` + raw counts + per-week trend.
- `--predicate P28` flag: walks every artifact that should cite
  `quality-ledger:` (heuristic: ADRs whose Decision section uses
  the phrases above) and reports any missing citations.

### 6. Backfill in same commit

The 6 ADRs receive `**Measurement source**: quality-ledger: pre_prod_share`
in their motivation chains, replacing the placeholder
`audit-predicate: P3` that under-cited their actual measurement target.

## Consequences

- **Plus**: Quality is now a first-class Goal. Future ADRs that fit the
  P3-family pattern get an obvious citation to use.
- **Plus**: incidents and pre-prod catches are computable from the same
  machinery the audit cycle already produces. No new logging burden.
- **Plus**: postmortems.md is no longer a folklore curiosity; it's a
  named Element on the motivation layer (Goal: Quality;
  Measurement source: quality-ledger).
- **Plus**: contribution-report's soft-orphan list closes (was 6
  zero-inbound Live ADRs; now they're traceable to Quality goal).
- **Minus**: pre_prod_share is approximate. Audit FAIL/WARN counts are
  not weighted by severity; a typo-warn and a privacy-leak-fail count
  the same. Mitigation: the ratio is a *trend signal*, not a precision
  instrument; weighting can land in a future ADR amendment if the
  trend signal alone proves insufficient.
- **Minus**: postmortems.md needs a Severity field per entry to
  separate Catastrophic / Major / Minor incidents. Today: equal
  weight. Future: a Severity bucket on each entry.

## Invariants

- A new artifact landing in forge that decides a P3-family question
  (test-env, rebuild discipline, single-source-of-truth, container
  isolation, etc.) without `**Measurement source**: quality-ledger: ...`
  is a P28 FAIL on the next audit walk.
- postmortems.md MUST be append-only. Entries are not edited; corrections
  land as new entries that cite the prior entry's date + symptom.
- The Quality metric formula MAY be refined in a future ADR amendment;
  the citation type `quality-ledger:` stays stable.

## Alternatives considered

- **Inline pre-prod-catch counts in each audit's summary table.**
  Rejected: the audit already lists FAIL/WARN findings in its findings
  section; counting them is a tool job, not a per-audit authoring job
  (per the no-synthesis-prose lesson from audit-2026-05-01v).
- **Make Quality a Driver, not a Goal.** Considered. Per ArchiMate §
  6.3.2, a Driver is "an external or internal condition that motivates
  an organisation to define its goals" — Quality is the goal those
  decisions reach for; the Driver is the underlying "incidents
  compound" condition. Goal is the right level.
- **Use a per-ADR Severity field instead of a global pre_prod_share.**
  Considered. Severity is useful but doesn't replace the share; the
  share is an at-a-glance trend signal. Severity can land later as a
  refinement.

## Follow-ups

- Severity bucket per postmortems.md entry (Catastrophic / Major / Minor).
  Bucket weighting in `pre_prod_share` formula.
- Per-ADR self-test: when a new ADR cites `quality-ledger:`, the audit
  walk should verify the corresponding postmortem story exists (i.e.,
  the ADR was motivated by a real incident, not a hypothetical).
- 30-day rolling window may be too short for a slow-cycle home-lab;
  consider 90-day after enough data.
- Wire `quality-report.py` output into audit-process.md's "Aggregate
  scores per agentic-md unit" table as a 13th row "Quality (system-wide)".
