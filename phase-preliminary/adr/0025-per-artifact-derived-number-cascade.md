# ADR 0025 — Per-artifact derived-number cascade; section name shortened; Goal re-cascade for ~30 chains

## Status

Accepted (2026-05-02). Active.

## Motivation

Per [P7](../architecture-principles.md):

- **Driver**: ADR 0023 set up OKR-shaped Goals with numerical KRs.
  ADR 0024 corrected Architect-velocity direction. But the cascade
  analysis (audit-2026-05-02b §F) showed: only 2 of 12 sampled
  chains cascade their per-artifact derived number INTO the cited
  Goal's KR. Most chains cite TTS or Architect-velocity but their
  measurement is actually a quality signal (runner pass rate, lab
  pass rate, predicate PASS). Architect call: "there must be derived
  numbers for each artifact." OKR framing is optional ("you can get
  rid of okrs if not needed"); derived numbers per artifact are
  mandatory.
- **Goal**: Architect-velocity (KR: ≤ 20 execution failures / 30-day).
- **Outcome**: every per-artifact chain has a `**Contribution**:`
  bullet stating the derived number relating the artifact to its
  cited Goal's KR; ~30 chains re-cascaded to the correct named Goal;
  section name shortened to `## Measurable motivation chain` (drop
  `(OKRs)` parenthetical per architect call); P30 added enforcing
  the Contribution bullet.
- **Measurement source**: audit-predicate: P30 (NEW; enforces
  Contribution bullet) + P29 (cascade integrity).
- **Contribution**: this ADR introduces P30 + reframes 71 chains;
  closes the cascade-completeness gap surfaced in audit-2026-05-02b;
  contributes to Quality KR by enabling per-artifact-level
  measurement (which feeds pre_prod_share via the audit cycle).
- **Capability realised**: Architecture knowledge management.
- **Function**: Add-derived-number-per-chain.

## Context

Three architect calls accumulated to this ADR:
1. "you can get rid of okrs if not needed" → drop the parenthetical
   from the section heading.
2. "there must be derived numbers for each artifact" → mandate the
   Contribution bullet.
3. "while I change architecture it's ok, no problem. when you cannot
   execute this architecture - it hurts my velocity" → re-cascade
   chains so per-artifact numbers actually map to the correct Goal
   (most runner pass rates → Quality, not TTS / Architect-velocity).

The sample analysis showed:
- Quality-cited chains (postmortems, container-runtime): cascade clean.
- TTS-cited chains with runner aggregates (wiki-pm, develop-wiki-product-line):
  WRONG cascade — runner pass rate is a quality signal, not a TTS signal.
- Architect-velocity-cited chains with runner pass rates (auditor): WRONG
  cascade — runner pass rate measures execution health, not failure count.
- Experiment-closure chains for K2: have a real number (2.7%) but it
  wasn't formally aligned to TTS KR's 0.30 target.

## Decision

### 1. Section name shortened — drop `(OKRs)` parenthetical

`## Measurable motivation chain (OKRs)` → `## Measurable motivation
chain` everywhere (127 files swept). Per architect call: "yes, since
there's no okrs )))". The OKR-style cascade IS still in effect (Goal
is the O cascade pointer; Measurement source is the per-artifact KR);
the section name is just shorter.

P24 + P26 + P29 + P30 signal regexes updated accordingly. ADR 0022
header text retained ("OKRs" appears in body for historical context).

### 2. New `**Contribution**:` bullet (mandatory)

Every per-artifact chain MUST include a `- **Contribution**:` bullet
between `**Measurement source**:` and `**Capability realised**:`.

Format:

```
- **Contribution**: <derived-number-or-pending> — <how-it-relates-to-cited-Goal-KR>
```

Examples:

```
- **Contribution**: runner: test-auditor-runner pass rate
  (35.0/38.0 = 0.921) — each PASS reduces a pre-prod bug class for
  the auditor role; aggregate contributes to Quality KR pre_prod_share
  via the audit catch-rate side of the formula.
```

```
- **Contribution**: experiment-closure: K2 → L1 ships 0.027 saved-time
  on real-A; L3 probe 0.216 projected; contributes 0.027 (current) →
  0.243 (projected if L1+L3 stack) toward TTS KR (target 0.30; gap
  0.057 if L3 lands).
```

```
- **Contribution**: pending TTS harness (CI cycle).
```

### 3. Goal re-cascade for ~30 chains

Per-class cascade rules:

| Artifact class | Was citing | Now cites | Reasoning |
|---|---|---|---|
| 6 Roles (auditor, wiki-pm, developer, devops, source-author, concept-curator) | TTS / mixed | **Quality** | Runner pass rate = quality of agent execution |
| 4 Lab AGENTS.md | Architect-velocity | **Quality** | Lab pass rate = quality of lab availability |
| Phase B Capabilities | mixed | **Quality** (mostly); **TTS** for product-line if directly applicable | Aggregate of runner-pass-rates IS quality signal |
| Phase B Products (kurpatov-wiki, wiki-product-line) | TTS (correct) | **TTS** (kept) | Customer-facing product → TTS |
| Phase D services + ADRs | Quality (mostly correct) | **Quality** (kept) | P3-family ⇒ Quality |
| Phase F K1/K2 | TTS (correct) | **TTS** (kept) | Wiki publication / compact-restore = TTS |
| Phase F G1/G2/G3 | Architect-velocity | **Quality** | Platform stability = quality |
| Phase A drivers/goals/vision | mixed | **Architect-velocity** | Declarative meta artifacts |
| Phase G postmortems | Quality (correct) | **Quality** (kept) | Incidents-side of pre_prod_share |
| Phase preliminary ADRs | mixed | **Quality** | Most ADRs prevent a bug class |
| Phase preliminary metamodel | Architect-velocity | **Architect-velocity** (kept) | Declarative reference |
| Phase H audit-process | Architect-velocity | **Architect-velocity** (kept) | Meta-process |

71 chains transformed by per-class script + 5 hand-fixed (org-units,
collaborations/kurpatov-wiki-team, components, data-sets,
adr/0002-data-outside-git).

### 4. Goal bullet now includes `(KR: ...)` clause

Format:
```
- **Goal**: <named Goal> (KR: <KR target>).
```

Example:
```
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
```

P29 unchanged in operation (still verifies named Goal cited); the KR
clause is a recommended-but-not-strict addition for at-a-glance
KR-quote.

### 5. New audit predicate P30 — Contribution bullet mandatory

Add **P30** to `audit-process.md`:

> **P30 — Per-artifact derived-number cascade.** Every per-artifact
> chain MUST include a `- **Contribution**:` bullet between
> `**Measurement source**:` and `**Capability realised**:` per ADR
> 0025 § Decision 2. Walks via:
> `python3 scripts/test-runners/goals-report.py --predicate P30`.
> Empty result = PASS.

P30 backfilled in same commit per the predicate-+-sweep-+-same-commit
pattern.

### 6. Code-block format roles converted to bullet format

`auditor.md` and `wiki-pm.md` used the older code-block chain format
(per ADR 0015 dec 1). Converted to bullet format in same commit so
the per-class transform applies uniformly. ADR 0015 dec 1's code-block
template superseded by bullet format per this ADR.

## Consequences

- **Plus**: every chain now has a derived number that explicitly
  relates to its cited Goal's KR. The cascade is real, not just
  structural.
- **Plus**: re-cascade puts ~30 chains under Quality (where they
  belong) instead of TTS / Architect-velocity (where they didn't fit).
  Quality KR's contribution side is now well-populated.
- **Plus**: shorter section name (saves 7 chars × 127 files).
- **Plus**: P30 is fail-closed; no new chain can land without a
  derived number.
- **Minus**: Contribution bullet is prose with embedded numbers,
  not pure machine-parseable. A Goal-KR rollup that sums Contribution
  values needs further parsing work. Mitigation: deferred — today
  the Contribution bullet is a per-artifact statement; per-Goal
  rollup landing in `goals-report.py` is queued (follow-up #1).
- **Minus**: 13 chains skipped by per-class transform (transitive /
  no chain) — confirmed transitive carve-outs.

## Invariants

- A new chain landing without `**Contribution**:` bullet = P30 FAIL.
- Goal-bullet KR clause is recommended; absent KR = no FAIL (just
  reduces at-a-glance utility).
- Re-cascade direction (runner pass rates → Quality) is permanent
  per architect call; reverting requires ADR amendment.

## Alternatives considered

- **Keep `(OKRs)` in section name** — rejected per architect call.
- **Make Contribution bullet machine-parseable JSON line** —
  considered. Rejected: prose readability matters; JSON inside md
  is awkward. Future tooling can parse the prose for numbers
  (regex-friendly) without enforcing JSON structure.
- **Auto-compute Contribution from Measurement source citation +
  current value** — considered (would eliminate manual authoring).
  Partially adopted: many Contribution bullets do quote the runner
  pass rate or experiment closure number. But the "how it relates
  to Goal KR" sentence is per-artifact-specific and requires
  understanding the artifact's role; not auto-generatable cleanly.

## Follow-ups

- **Per-Goal rollup in `goals-report.py`** (#1) — sum the
  per-artifact Contribution values into the system-level Goal KR
  computation. Today the rollup is heuristic (Quality KR derives
  from audit FAIL/WARN counts, not from per-artifact runner aggregates).
  Future: parse Contribution bullets, aggregate where the formula is
  stable.
- **Contribution-formula linter** (#2) — verify that every chain's
  Contribution mentions the cited Goal's KR formula or "pending"
  with reason. P30 only checks existence; formula-conformance is
  a future tightening.
- **Code-block-format chains in other phases** — only auditor +
  wiki-pm used it; the other 6 Roles already use bullet format.
  No further conversion needed.
