# Framework tailoring

What forge adopts from TOGAF / ArchiMate and what it deliberately
does not.

## Adopted

- **TOGAF ADM phase vocabulary and layering.** Forge organizes its
  documentation by classic TOGAF ADM phases (Preliminary, A — H).
  This is the structural backbone every reader navigates by.
- **ArchiMate 4 vocabulary across all phases** (extended in
  [ADR 0014](adr/0014-archimate-across-all-layers.md); language
  itself described in [`archimate-language.md`](archimate-language.md);
  forge → ArchiMate mapping in [`archimate-vocabulary.md`](archimate-vocabulary.md)). Forge
  uses ArchiMate 4 as its modeling vocabulary throughout the
  TOGAF phases — every named element (Role, Capability,
  Application Component, Plateau, etc.) maps to one ArchiMate 4
  type per the cross-reference table in
  [`archimate-vocabulary.md`](archimate-vocabulary.md).
  Relationships use the typed verbs from §5 of the spec
  (Aggregation, Composition, Assignment, Realization, Serving,
  Access, Influence, Association, Triggering, Flow,
  Specialization). Trajectories attach to service / capability
  quality dimensions and are typed as a pair of Plateaus +
  Work Package + Deliverables (Implementation & Migration
  domain). Replacing a component (vLLM 0.19 → 0.20) is the
  next step on the same trajectory — the System Software
  changes; the Capability and the Function it realizes do not.
  The pre-2026-04-30 narrower scope ("ArchiMate vocabulary
  inside Phase D") is superseded by ADR 0014.
- **Capability vocabulary inside Phase B.** What forge can do is a
  *capability*; what produces shippable output for users is a
  *product*; the org units are a separate axis. These three are
  linked but each lives in its own file under
  [`../phase-b-business-architecture/`](../phase-b-business-architecture/).
- **Per-phase ADRs.** Architectural decisions live in the phase
  whose layer the decision changes. Forge-level ADRs in
  `forge/phase-<x>/adr/`; lab-scoped ADRs in
  `<lab>/docs/adr/` or `<lab>/adr/`. Every
  per-lab AGENTS.md cites its ADRs by phase.

## Deliberately skipped

- **Formal TOGAF deliverables.** No Architecture Vision Statement
  document, no Architecture Definition Document, no Architecture
  Roadmap as separate artefacts. Each phase's content lives in
  that phase's folder; the synthesis lives in
  [`../AGENTS.md`](../AGENTS.md).
- **TOGAF certification.** This is a single-architect home-lab;
  the structure is for personal clarity, not for an external
  certifier.
- **ArchiMate diagrams as deliverables.** Vocabulary yes; diagrams
  no. Pictures bit-rot faster than prose at this scale.
- **The full ADM cycle as a calendar process.** We do not run
  scheduled ADM iterations. A "phase" here is a folder, not a
  meeting. Architecture work happens continuously, driven by
  metric gaps surfaced in Phase E and closed in Phase F.
- **Governance bodies.** No Architecture Board, no Architecture
  Review Board. The architect of record is the only governance
  body — see [`architecture-team.md`](architecture-team.md).

## Why this tailoring

The point of TOGAF here is **layering**: a decision about wiki
concept structure (Phase B) lives one layer below "Forge saves
human time" (Phase A), and a decision about which embedding model
(Phase D) lives two layers below that. When a reader opens
[`../AGENTS.md`](../AGENTS.md) they do not have to wade through
libblas3 to reach the mission; when they debug `embed_helpers.py`
they do not have to re-derive why the wiki exists.

The pieces of TOGAF that are about *organizational ceremony*
(boards, deliverables, calendar cycles) do not apply at single-
architect scale. The pieces that are about *vocabulary and
layering* are the bulk of TOGAF's actual value here, and that is
what we adopt.
