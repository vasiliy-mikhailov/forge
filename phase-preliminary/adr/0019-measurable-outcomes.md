# ADR 0019 — Every measurable motivation chain Outcome cites a measurement source

## Status

Accepted (2026-05-02). Active.

## Measurable motivation chain
Per [P7](../architecture-principles.md):

- **Driver**: post-2026-05-01u + 2026-05-01w sweeps, every
  in-scope artifact in forge has a `## Measurable motivation chain`
  section. But running
  `scripts/test-runners/motivation-measurability-report.py`
  surfaced **34 of 116 artifacts have prose Outcomes with no
  cited measurement source** — chains exist, but a reader
  cannot pull a current Level for the current commit. The
  same root cause as pre-P7: enforcement was piecemeal (Roles
  via test runners; tests via Reward functions; R-NN via
  catalog Status), no first principle universalised it.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: every measurable motivation chain Outcome cites a
  **measurement source** in a strict format the report
  parses; the report is GENERATED (no per-artifact authoring
  of "current level" prose); P26 fails-closed on missing
  citations.
- **Measurement source**: audit-predicate: P26 (the predicate
  this ADR adds; walks every chain via
  `motivation-measurability-report.py --gaps-only`; empty
  result = PASS). Post-commit: 0 GAPs.
- **Contribution**: ADR enforces a discipline that prevents one bug class; contributes to Quality KR via reduced incidents.
- **Capability realised**: Architecture knowledge management
  ([../../phase-b-business-architecture/capabilities/forge-level.md](../../phase-b-business-architecture/capabilities/forge-level.md)).
- **Function**: Universalise-Outcome-measurability.

## Decision

### 1. Standard measurement-source citation format

Every `## Measurable motivation chain` (or `## Motivation`) section adds
a new line directly after the `**Outcome**:` bullet:

```
- **Outcome**: <prose end-result>.
- **Measurement source**: <citation>
```

Where `<citation>` is one of:

| Citation | Meaning | Current-value lookup |
|---|---|---|
| `runner: <stem>` | A `scripts/test-runners/test-<stem>-runner.py` runner produces the score | `_score_history` aggregate |
| `runner-aggregate: <stem1>, <stem2>, ...` | Sum of multiple runners (e.g., a Capability aggregating its realising Roles) | mean of cited runners |
| `lab-tests: <code>` | One of the 4 labs' AGENTS test set (RL, WB, WC, WI) | `aggregate_per_lab` |
| `audit-predicate: P<NN>` | An audit-process predicate produces a binary or scored verdict | latest audit's findings for P<NN> |
| `catalog-row: R-<phase>-<slug>` | An R-NN trajectory row in `catalog.md` | row's Status / Level cells |
| `experiment-closure: <id>` | A Phase F experiment's closure verdict | experiment spec's Execution log |
| `corpus-walk: WP-<NN>` | A Wiki PM corpus-walk metric (S1/S2 counts) | WP runner output |
| `customer-cycle: CI-<N>` | A customer-interview cycle artifact (post-CI-1..7 run) | per-persona ledger counts |
| `n/a — declarative: <reason>` | The artifact is informational (no quantitative Outcome) | n/a (carve-out) |
| `quality-ledger: <metric>` | Reads incident count from postmortems.md `***`-entries + pre-prod-catch count from audit FAIL/WARN findings (ADR 0021) | `quality-report.py` output |
| `n/a — pending: <eta>` | Not yet measurable; ETA + reason cited | n/a |

The report walks every chain and the tooling resolves the
current value automatically — never authored by hand into the
artifact (per the no-synthesis-prose lesson from
audit-2026-05-01v).

### 2. P26 — fail-closed enforcement

Add **P26** to
[`audit-process.md`](../../phase-h-architecture-change-management/audit-process.md):

> **P26 — Universal Outcome measurability.** For every
> measurable motivation chain (matched by P24's scope), the chain's
> Outcome MUST be followed by a `**Measurement source**:`
> line citing one of the formats in ADR 0019 decision 1.
> Missing citation = `FAIL`.

P26 walks via `motivation-measurability-report.py --gaps-only`
which already enumerates the gaps. Empty result = P26 PASS.

### 3. Report tool extended

`scripts/test-runners/motivation-measurability-report.py`
parses the new line preferentially. When a chain has
`**Measurement source**: runner: test-wiki-pm-runner`, the
report shows `33/33 = 1.000 PASS`. When it says
`n/a — declarative: ...`, the report shows `n/a`. The 34
gaps disappear from the GAPs list.

### 4. Backfill landing in same commit

All 34 gap chains receive their `**Measurement source**:`
line in this commit (per the "predicate + sweep + same
commit" pattern from ADR 0017's P24 introduction).
Categories:

| Phase | Files | Common citation |
|---|---|---|
| A — drivers, goals | 2 | `audit-predicate: P18` / `P19` |
| B — Capabilities (4) | 4 | `runner-aggregate: ...` (the realising-role runners) |
| B — Products (5) | 5 | `experiment-closure: K1/K2` or `runner-aggregate` |
| B — other | 2 | `n/a — declarative` (org-units) / `runner-aggregate` (collab) |
| C — catalogs (2) | 2 | `audit-predicate: P9` / `n/a — declarative` |
| D — files (8) | 8 | mix of `lab-tests: ...` (smoke health), `audit-predicate: P3/P4`, `n/a — declarative` |
| E — roadmap | 1 | `experiment-closure: K1, K2, G1, G2, G3` |
| F — experiments + plan (5) | 5 | `experiment-closure: <id>` (each experiment cites its own closure) |
| G — files (5) | 5 | `runner: test-devops-runner` (operations); `audit-predicate: P9` (lab-AGENTS-template); `n/a — declarative` (governance.md, policies) |

### 5. Future ADRs MUST include the line

ADR 0017 already required `## Motivation` for new ADRs from
0017+. ADR 0019 extends: future ADRs' Motivation section MUST
include a `**Measurement source**:` line. This ADR is the
first; ADR 0019 itself includes it (per § Motivation above).

## Consequences

- **Plus**: every artifact's current Level is one report-run
  away. No cross-tab bookkeeping in prose.
- **Plus**: regressions become diff-able — re-running the
  report at two commits shows which artifacts moved.
- **Plus**: forge-as-public-reference becomes more useful: any
  architect adopting forge's method gets an at-a-glance
  measurement view per artifact.
- **Minus**: one extra line per chain. Cheap; offset by the
  generated current-value lookup eliminating per-artifact
  current-value prose.
- **Minus**: the citation format must stay stable; changes
  require an ADR amendment + report-tool update.

## Invariants

- A new measurable motivation chain landing in forge without a
  `**Measurement source**:` line is a P26 FAIL on the next
  audit walk.
- Citation format changes require an ADR amendment; tooling
  must be backwards-compatible (old citations keep working
  while new ones land).
- The report is the single source of truth for current Level;
  no per-artifact "current value" prose (per the
  audit-2026-05-01v synthesis-deletion lesson).

## Alternatives considered

- **Generate the citation from artifact path heuristics** (no
  per-chain line). Rejected: the heuristic is brittle (the
  current report does this and gets 34 wrong); explicit
  citation in the chain is more honest and survives refactors.
- **Inline current-value prose in each chain** (handwritten).
  Rejected: stale-decay (per audit-2026-05-01v synthesis
  deletion). Generated viewpoint is the right answer.
- **Make P26 WARN-only initially** (soft launch). Rejected:
  the same-commit sweep makes it practical to land FAIL-closed
  immediately, matching the P7 → P24 pattern.

## Follow-ups

- Audit-process P22 + AU-11: extend the aggregate table to
  include a "Measurement coverage %" column showing how many
  artifacts' current Level is computed vs unknown.
- Future quarterly review: re-run report; identify chains
  whose Level has been stuck at the same value for ≥ N
  walks (stalled trajectory signal).
- The report could emit a JSON manifest the audit consumes
  directly (instead of the audit re-running the walk).
