# ADR 0023 — Top-level Goals carry numerical KRs; per-artifact chains cite a named Goal (OKR cascade)

## Status

Accepted (2026-05-02). Active.

## Motivation

Per [P7](../architecture-principles.md):

- **Driver**: ADR 0022 renamed `## Motivation chain` → `## Measurable
  motivation chain (OKRs)`. The architect's response was sharp: "the
  only problem: it's not measurable))) you changed only name, but
  there are no numbers." Correct. Renaming the section without
  attaching numerical targets to the top-level Goals = cosmetic
  change. The KR side of OKR is missing at the system level, so per-
  artifact chains have nothing to cascade to.
- **Goal**: Architect-velocity → KR: ≥ 50 corrective actions / 30-day
  rolling (this ADR IS one corrective action per the metric).
- **Outcome**: 5 top-level Goals (TTS, PTS, EB, Architect-velocity,
  Quality) each carry a numerical Key Result (target + window + how
  measured); every per-artifact chain `**Goal**:` bullet cites
  exactly one named Goal; KRs cascade from system level (goals.md) to
  per-artifact level (`**Measurement source**:` value).
- **Measurement source**: audit-predicate: P29 (NEW; every Goal in
  goals.md has Target line; every chain Goal-bullet cites one of 5
  named Goals).
- **Capability realised**: Architecture knowledge management.
- **Function**: Add-numerical-KRs-to-top-level-Goals.

## Context

OKR (Objectives + Key Results) is the de-facto industry standard for
goal cascading: a system-level KR is decomposed into team-level KRs
which decompose into individual KRs, and each level's progress rolls
up. ADR 0022 named the chain section accordingly but didn't add the
KR numbers.

ArchiMate § 6.4.2 says Outcome is "tangible, possibly **quantitative**,
time-related" — the spec specifically allows numerical targets. The
chain Outcome bullet was always permitted to be quantitative; today
most are qualitative. This ADR codifies: top-level Goals MUST be
quantitative; per-artifact Outcomes MAY remain qualitative IF their
`**Measurement source**:` value supplies the quantitative KR.

Architect-set targets (per architect call 2026-05-02):
- TTS ≥ 30%
- PTS ≥ 30%
- Quality (`pre_prod_share`) ≥ 0.95
- EB = unit economics (revenue/cost ratio per published source)
- Architect-velocity = number of corrective actions taken

## Decision

### 1. 5 top-level Goals with explicit Target / Window / How-measured

`phase-a/goals.md` rewritten as a 5-row table (one row per Goal). Each
row carries: Objective | Key Result (formula + target) | Window | How
measured | Current. Per architect call:

| Goal | KR target | Window |
|------|-----------|--------|
| TTS | `tts_share ≥ 0.30` | per-use, rolling 30-day mean |
| PTS | `pts_share ≥ 0.30` (engagement × tts_share / theoretical_max) | rolling 30-day |
| EB | `unit_economics ≥ 1.0` (revenue_per_source / cost_per_source) | rolling 30-day |
| Architect-velocity | `corrective_actions ≥ 50 / 30-day` | rolling 30-day |
| Quality | `pre_prod_share ≥ 0.95` | rolling 30-day |

### 2. Cascade rule — per-artifact chains cite a named Goal

Every chain's `**Goal**:` bullet MUST cite exactly one of:
{`TTS`, `PTS`, `EB`, `Architect-velocity`, `Quality`}. Recommended
format:

```
- **Goal**: <named Goal> (KR: <named Goal's KR target>).
```

Example:

```
- **Goal**: Architect-velocity (KR: ≥ 50 corrective actions / 30-day).
```

Existing chains may use the shorter `- **Goal**: <named Goal>` —
P29 verifies the named Goal is one of the 5; the explicit KR-quote
is recommended (auto-checked by future tooling) but not required.

### 3. New audit predicate P29

Add **P29** to `audit-process.md`:

> **P29 — OKR cascade integrity.** (a) Every Goal row in `phase-
> a/goals.md` MUST have Target / Window / How-measured cells filled
> (Current MAY be `n/a — pending`). (b) Every per-artifact `**Goal**:`
> bullet MUST cite exactly one of the 5 named Goals (TTS, PTS, EB,
> Architect-velocity, Quality). Walks via:
> `python3 scripts/test-runners/goals-report.py --predicate P29`.
> Empty result = PASS.

P29 backfilled in same commit per the predicate-+-sweep-+-same-commit
pattern from ADR 0017 / 0019 / 0021 / 0022.

### 4. New tool — goals-report.py

`scripts/test-runners/goals-report.py`:
- Parses `goals.md` for the 5 Goal rows + their KR formulas.
- Computes current values:
  - TTS: pending until CI cycle measurement harness lands.
  - PTS: pending until cohort engagement telemetry lands.
  - EB: pending until eb-report.py.
  - Architect-velocity: counts `*Taken:*` lines in postmortems +
    closed FAIL/WARN findings in audits within window.
  - Quality: defers to `quality-report.py` for current
    `pre_prod_share`.
- Emits one row per Goal: Target / Current / Band (PASS / italian-strike
  / FAIL / pending).
- `--predicate P29` walks all chains for the cascade-integrity check.

### 5. Targets ratchet after first month

The targets above are conservative starting positions. Per the ratchet
discipline: after the first month of stable measurement, each Goal's KR
is reviewed and may be raised by ADR amendment. The mechanism:
quarterly review of `goals-report.py` historical output → architect
call → ADR amendment landing the new target.

### 6. ADR 0022's section-rename amended

ADR 0022's body says "every chain section across forge renamed to
`## Measurable motivation chain (OKRs)`; section name now declares
the structural contract (Outcome + Measurement source = O + KR)." This
ADR (0023) completes that promise: the KR side now exists at top-level
goals.md AND per-artifact chains cascade to it. The structural contract
is no longer aspirational.

## Consequences

- **Plus**: real measurability, not cosmetic. `goals-report.py` is the
  one-command lookup for system-level OKR status.
- **Plus**: per-artifact chains' `**Goal**:` bullet becomes a strict
  cascade pointer. P29 catches drift (new chain citing an unnamed
  Goal = FAIL).
- **Plus**: aligns forge with industry-standard OKR practice, easier
  to communicate to OKR-literate readers.
- **Minus**: 3 of 5 KRs are pending measurement infrastructure (TTS
  harness, PTS cohort telemetry, EB unit-economics calculator). Today
  only 2 of 5 (Architect-velocity, Quality) have live current values.
  Mitigation: `pending` is an honest state per the P26 measurement-
  source citation table; doesn't block P29.
- **Minus**: targets are conservative starting positions; quarterly
  ratchet is needed to keep them stretchy. Without ratchet, the
  bands lose meaning.
- **Minus**: forces a small chain-cascade sweep on existing chains
  whose `**Goal**:` bullet uses old wording (e.g. "Architect-
  velocity (Phase A)" — keep, "Phase A" is the column not the Goal)
  vs. ones that don't cite a named Goal at all.

## Invariants

- A new chain landing in forge whose `**Goal**:` bullet doesn't cite
  one of the 5 named Goals = P29 FAIL.
- A new top-level Goal landing in goals.md without Target + Window +
  How-measured = P29 FAIL.
- Targets are revisable via ADR amendment only (not by editing
  goals.md directly without a corresponding ADR — this prevents
  silent target drift).
- Current values are GENERATED by `goals-report.py`, NOT authored by
  hand into goals.md (per the no-synthesis-prose lesson from
  audit-2026-05-01v).

## Alternatives considered

- **Set targets at industry-standard OKR ratios (e.g. 0.7 = success;
  1.0 = stretch)**. Rejected: forge isn't yet at the maturity where
  rich OKR ratios add signal beyond simple ≥ thresholds. Ratchet later.
- **Cascade to per-Capability KRs first, per-artifact KRs second**.
  Considered: more correct ArchiMate decomposition. Rejected for now:
  Capability layer doesn't currently aggregate KR rollups, just runner
  aggregates. Adding a Capability-KR layer is a bigger change; this
  ADR keeps the cascade flat (Goal → artifact) until per-Capability
  KR-rollup is needed.
- **Make `**Goal**:` bullet a strict enum with no free text**. Rejected:
  the qualitative parenthetical (e.g. "Architect-velocity → KR: ≥ 50
  corrective actions / 30-day") is useful for at-a-glance KR-quote;
  the enum check is on the named Goal token only.

## Follow-ups

- Build `eb-report.py` once real GPU spend + architect-time tracking
  is in place (queued as ADR 0023 follow-up #1).
- Build TTS harness once K1 v2's published wiki is ready for timed
  read-sessions × persona (queued as ADR 0023 follow-up #2; depends
  on the customer-interview cycle from ADR 0016 + the persona
  expansion underway in commit `c31593c`).
- Quarterly KR-ratchet review (queued as ADR 0023 follow-up #3).
- Expose top-level Goal current values in audit findings'
  "Aggregate scores" table (today shows agentic-md unit aggregates;
  add a "Goals" section with the 5 KRs).
