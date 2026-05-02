# Goals

Motivation-layer per ArchiMate § 6.4.1; quantified as OKRs per ADR 0023.
Each Goal carries an Objective (qualitative direction) + Key Result
(numerical target with window). Every per-artifact chain's `**Goal**:`
bullet MUST cite one of these 5 named Goals; `**Measurement source**:`
value is the per-artifact KR contributing to the named Goal's KR.

| Goal | Objective (O) | Key Result (KR) | Window | How measured | Current |
|------|---------------|-----------------|--------|--------------|---------|
| **TTS** — Theoretical Time Saved | A reader extracts the same understanding from the wiki in less time than from the source lecture | `tts_share = (source_duration − wiki_read_time) / source_duration ≥ 0.30` | per-use, rolling 30-day mean | TBD harness: timed wiki-read sessions × persona vs. lecture duration; pending CI-1..7 cycle output | n/a — pending first cohort |
| **PTS** — Practical Time Saved | TTS savings actually realised across the user cohort, not just theoretical | `pts_share = (Σ tts_share × engagement) / theoretical_max ≥ 0.30` (engagement = % of cohort that completes ≥ 1 wiki read per source) | rolling 30-day | TBD — needs CI cycle telemetry; today no users yet | n/a — pending cohort |
| **EB** — Economic Balance | Per-unit unit economics positive: revenue/cost ratio ≥ 1.0 (product self-sustains at scale, not just architect's hobby budget) | `unit_economics = revenue_per_published_source / cost_per_published_source ≥ 1.0` (cost = GPU-hours × electricity rate + storage + architect-time × shadow rate; revenue = theoretical pricing × engagement) | rolling 30-day | `scripts/test-runners/eb-report.py` (queued; today computed manually from K1 v2 wall-time × electricity + architect log) | n/a — pending eb-report.py |
| **Architect-velocity** | TOGAF operationalises **architecture** execution. Architect CHANGES architecture (ADRs, renames, new Goals) — that's the job, not a cost. The cost is when **the agent cannot execute the (clear) architecture** and the architect has to manually fix what should have been autonomous. **Execution failure is the cost.** | `execution_failures ≤ 20 / 30-day rolling` (LOWER = BETTER; ratchet down to ≤ 5 once scheduled tasks land). Execution failure = commit message contains "architect call" / "per architect" / "architect-deferred" but is **NOT** an ADR landing (ADRs are architecture changes, not failures). | rolling 30-day | `goals-report.py` greps git log; ADR landings excluded | TBD per run |
| **Quality** | Bugs are caught before they reach the lab; pre-prod gate works | `pre_prod_share = pre_prod_catches / (pre_prod_catches + incidents) ≥ 0.95` | rolling 30-day | `scripts/test-runners/quality-report.py` (per ADR 0021) | **0.667** (28/42, 365-day; 30-day window n/a until enough audit walks) |

Initial targets are **conservative starting positions**, not final — per
ADR 0023 § Decision 5 they ratchet up after the first month of stable
measurement. Current values come from `goals-report.py` (queued); KRs
are recomputed at every audit walk.

The 5 Goals form the OKR cascade: every per-artifact `**Goal**:` bullet
cites exactly one of {TTS, PTS, EB, Architect-velocity, Quality}; the
artifact's `**Measurement source**:` value is the per-artifact KR
contributing to the named Goal's system-level KR.

## Measurable motivation chain

Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: every action choice must be evaluated against named
  Goals (P5); without a Goals catalog with numerical targets,
  "metric-driven action" has no metrics.
- **Goal**: Architect-velocity (KR: ≤ 20 execution failures / 30-day).
- **Outcome**: every artifact's chain has a named Goal that traces to
  this file; this file has a numerical KR per Goal; `goals-report.py`
  computes current values; the next architect-velocity walk is one
  command away.
- **Measurement source**: audit-predicate: P19 (every Goal has ≥ 1
  realising R-NN trajectory) + P29 (every Goal has Target line; every
  chain cites a named Goal — per ADR 0023).
- **Contribution**: declarative Phase A artifact; contributes to A-V KR by anchoring downstream cascade.
- **Capability realised**: Architecture knowledge management.
- **Function**: Catalogue-Phase-A-Goals-with-Targets.
- **Element**: this file (5 Goal rows with Target + Window + How
  measured + Current cells).
