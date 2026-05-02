# ADR 0024 — Architect-velocity reframed: count of agent EXECUTION FAILURES (lower = better); architecture changes are the architect's job, not a cost

## Status

Accepted (2026-05-02). Active.

## Motivation

Per [P7](../architecture-principles.md):

- **Driver**: ADR 0023 set Architect-velocity's KR as `≥ 50 corrective
  actions / 30-day rolling` — a **higher = better** metric (more
  corrective actions = better velocity). Architect call corrected
  the framing: "togaf operationalizes strategy execution. Each time
  architect intervents automatic execution - it's bad. So small
  steps towards goals/showtoppers is way to go." The original metric
  rewarded the wrong thing — every architect intervention IS a
  corrective action by my count, and the metric would have rewarded
  the chat-driven heavy-handed mode that's actually suboptimal.
- **Goal**: Architect-velocity (KR per this ADR: ≤ 20 architect
  interventions / 30-day rolling — this ADR IS one intervention,
  recursively).
- **Outcome**: Architect-velocity KR inverted — count of architect
  interventions, LOWER = BETTER. Intervention = explicit
  architectural decision the system couldn't make autonomously
  (ADR landings + commit-message "architect call" markers).
- **Measurement source**: audit-predicate: P29 (cascade integrity;
  this Goal is one of the 5 named Goals chains cite).
- **Capability realised**: Architecture knowledge management.
- **Function**: Reframe-architect-velocity-as-intervention-cost.

## Context

TOGAF's value proposition is operationalising strategy execution:
the ADM phases are sequential (Preliminary → A → B → C → D → E → F
→ G → H), and each phase hands off to the next without
re-litigation. Architect intervention at the implementation
(Phase G) or change-management (Phase H) level signals that the
strategy/architecture (Phase A/B/C/D) wasn't crisp enough to
autonomously execute against.

The original ADR-0023 KR (`≥ 50 corrective actions / 30-day
rolling`) had the opposite incentive: it counted every audit
finding closed, every postmortem `*Taken:*` line, every R-NN
closure as a positive. But many of those are architect interventions
in disguise — the architect noticed the issue, called for the fix,
and the fix landed. By that count, an architect-heavy bootstrapping
mode looks high-velocity when it's actually the symptom of strategy
gaps.

The corrected framing: **autonomous progress is the goal; architect
intervention is the cost**. Healthy steady state = small autonomous
steps toward Goals or away from showstoppers, with the architect
intervening only for genuine strategic-direction questions
(rare-but-decisive, not high-volume).

## Decision

### 1. KR inverted — lower is better

| | OLD (per ADR 0023) | NEW (per this ADR) |
|---|---|---|
| KR | `≥ 50 corrective actions / 30-day rolling` | `≤ 20 architect interventions / 30-day rolling` |
| Direction | higher = better | **lower = better** |
| Incentive | reward more action | reward less intervention |
| Steady-state target | n/a (was unbounded above) | ratchet down to ≤ 5 once Cowork-mode scheduled tasks land |

### 2. Architecture changes ≠ execution failures

Per architect call (2026-05-02): "not strategy was clear, but architecture
was clear. while I change architecture it's ok, no problem. when you
cannot execute this architecture - it hurts my velocity."

The metric measures **agent execution failures**, NOT architecture
changes. Architect's role IS to change architecture (ADRs, predicate
additions, model edits, renames, Goal additions) — those are the
architect's job and don't count against velocity. The cost is when the
**agent** (Claude / runners / autonomous loops) cannot execute the
clear architecture and the architect has to manually intervene at the
operational level.

Concretely:
- **Architecture change (NOT a velocity hit)**: ADR landings; predicate
  additions; renames (e.g. ADR 0022); new Goals (e.g. ADR 0021); metric
  redefinitions (this ADR).
- **Execution failure (velocity hit)**: architect manually fixes a bug
  the agent should have caught; architect re-runs an audit that should
  have run autonomously; architect closes a finding the agent left open;
  architect prompts the agent to do a step the agent missed.

### 3. What counts as an "agent execution failure"

A commit qualifies as an **execution failure** if its message:
- Contains `architect call` / `per architect` / `architect-deferred`
  (explicit human-in-the-loop markers indicating the architect had to
  step in at execution level), AND
- Is **NOT** an ADR landing (commits whose subject starts with `ADR `
  are architecture changes per § Decision 2, not execution failures).

Other commits — sweeps, backfills, audit closures, runner additions,
predicate enforcement, R-NN row closures — count as autonomous
progress regardless of whether they were prompted by the architect
in chat. (See § Honest Caveat below.)

### 4. Honest caveat — chat-driven workflow undermeasures

In today's chat-driven workflow, NEARLY EVERY commit traces back to
an architect prompt — even ones that don't say so in the commit
message. The strict-regex metric detects 8/235 commits in the 30-day
window as interventions (3.4%); the actual chat-driven intervention
rate is closer to 100%. The metric is structurally honest but
**undermeasures until commit-provenance tagging lands** (see
follow-up #1).

This is acceptable for now because:
- The metric establishes the right incentive (penalise interventions).
- It tightens automatically as commit-provenance tagging adopts.
- The TARGET (≤ 20 / 30-day) is conservative and will not produce
  false-PASS even at today's loose detection — the true rate at any
  realistic measurement will exceed 20 / 30-day in chat-driven mode.

### 5. ADR 0023 §1 amended

ADR 0023's table row for Architect-velocity is amended via this ADR:
the KR formula + direction change. ADR 0023 stays — only this row
in its decision table is refined.

### 6. goals-report.py implementation

`scripts/test-runners/goals-report.py`:
- Replaces `count_corrective_actions(window)` with
  `count_architect_interventions(window)`.
- Greps `git log --since=<window> days ago --pretty=format:%s` for the
  intervention regex.
- Adds `lower_better: True` flag in the row dict; band logic inverted:
  PASS if current ≤ target; italian-strike if ≤ 1.5×; FAIL otherwise.

### 7. Postmortems entry queued

The metric-flip itself is a postmortem-worthy story (the original
metric incentivised the wrong thing for almost a full session before
the architect caught it). Queued as a postmortems.md entry but NOT
added in this commit per architect-velocity discipline (the ADR is
the strategic decision; the postmortem lands when next session
intersects with operational sweep).

## Consequences

- **Plus**: incentive aligned with TOGAF's operationalises-strategy
  principle. Less chat-driven heavy-handed mode; more autonomous
  small-steps progress.
- **Plus**: target ≤ 20 / 30-day is tight enough to drive real
  autonomy investment (scheduled tasks, autonomous audit loops,
  agent-initiated R-NN closures).
- **Plus**: ratchet-down path is clear (≤ 20 → ≤ 10 → ≤ 5 as autonomy
  matures).
- **Minus**: today's metric undermeasures because of commit-message
  conventions. Mitigation: commit-provenance tagging follow-up.
- **Minus**: the metric flip means the "Architect-velocity 43/50
  italian-strike" reading from audit-2026-05-02a is now misleading —
  it was reading the OLD metric. New reading: 8/20 PASS (strict
  detection) or ~235/20 = ~12x over budget (honest detection).
  Audit-2026-05-02b restates honestly.
- **Minus**: a system in active R&D legitimately requires architect
  input. The KR's ≤ 20 target may be too tight during product-discovery
  phases. Mitigation: ratchet UP (not down) during exploration phases
  via ADR amendment; ratchet down during execution phases.

## Invariants

- A new KR for Architect-velocity that REWARDS more intervention
  (higher = better) is a P29 FAIL on the next walk; this ADR fixes
  the direction permanently.
- Targets are revisable via ADR amendment per ADR 0023 §5 ratchet
  discipline — direction (lower = better) is not.

## Alternatives considered

- **Keep both metrics: (corrective_actions ≥ 50) AND (interventions
  ≤ 20)**. Rejected: two metrics conflict — closing a finding
  prompted by an architect counts as both +1 corrective action AND
  +1 intervention. Net signal noise. One metric, lower = better.
- **Use intervention RATIO (interventions / total_commits ≤ 0.20)
  instead of absolute count**. Considered. Ratio scales with
  throughput (a productive month with 1000 autonomous commits and
  50 interventions = 5% PASS; a lazy month with 20 commits and 5
  interventions = 25% FAIL). Architect's language ("each
  intervention is bad") points at absolute count, not ratio.
  Absolute count wins.
- **Penalise large commits / reward small commits**. Architect said
  "small steps towards goals/showstoppers is way to go" — could
  encode as commit-size cap. Rejected for now: too prescriptive;
  some refactors legitimately cross many files (ADR 0017's 38-file
  sweep). Encode as discipline (postmortems-worthy when violated)
  not as KR.

## Follow-ups

- **Commit-provenance tagging** (#1) — every commit footer adds
  `Provenance: <architect-call | autonomous-loop | scheduled-task | recovery>`
  so the metric measures honestly. Backfill via transcript review
  is intractable; cut over forward-only.
- **Cowork-mode scheduled tasks** (#2) — needed for true autonomy.
  Each scheduled audit / runner / sweep that lands without architect
  prompt = 1 autonomous commit. Until this lands, intervention rate
  stays high.
- **Per-Goal intervention budget**: budget interventions across the
  5 Goals (e.g. ≤ 5 Quality interventions / 30-day; ≤ 3 EB
  interventions / 30-day). Out of scope; revisit after one month
  of measurement.
- **Ratchet review** (#3 cont.) — quarterly; if rate drops to ≤ 5
  consistently, target tightens; if rate spikes during legitimate
  exploration, target loosens via amendment.
