# Requirements Management

In the TOGAF ADM diagram this sits at the **center** of the circle:
not a phase you do once but a **continuous activity** that runs
across every phase. Phases A through H feed requirements into the
hub; the hub assigns them back out to the phase that should
address them; closed requirements promote per Phase H's trajectory
model.

Strategy & Motivation phases (Preliminary, A, B, H) **emit**
requirements. Implementation & Migration phases (E, F, G)
**absorb** them. The Core Layers (B, C, D) are where requirements
take physical shape as capabilities, application components,
technology services.

## How forge realises Requirements Management

A "requirement" in forge is a **quality-dimension trajectory** —
the gap between Level 1 (today) and Level 2 (next planned state)
on some metric, attached to either:

- a **capability** (Phase B, e.g. "Service Operation /
  throughput / 47 → ≥100 tok/s"), or
- a **technology service** (Phase D, e.g. "Vector retrieval /
  per-call cost / ~5 s/call → daemonized").

Goals from Phase A (TTS, PTS, EB, Architect-velocity) are the
**top-level requirements**. Each Level 2 target a Phase B / Phase
D trajectory carries must roll up to one of those goals.

Phase F experiment specs (`phase-f-migration-planning/experiments/<id>.md`)
are the **closure attempts**: hypothesis (IF–THEN–BECAUSE),
falsification criteria, sequenced work. A closed experiment
either promotes Level 2 to the new Level 1 (requirement met) or
falsifies and the requirement stays open — possibly with a new
sub-requirement added (e.g. G3 closure surfaced "contract
enforcement before model swap" as a new req).

So in forge the requirements catalog is not a separate database —
it is the **union of open quality-dimension trajectories** across
Phase B and Phase D, plus any open Phase A goals not yet decomposed
into trajectories.

## Layout

- [`catalog.md`](catalog.md) — current open + recently closed
  requirements, indexed by ID. Each has source phase, target
  phase that addresses it, and status.
- [`process.md`](process.md) — how a requirement enters the
  catalog, gets routed to a Phase F experiment, and exits.
- [`wiki-requirements-collection.md`](wiki-requirements-collection.md) —
  the wiki-specific *front-end* to `process.md`: how the architect
  (wearing the wiki PM hat) discovers requirements for a new wiki
  product from the raw corpus + reader needs, before the general
  lifecycle takes over. Realises the Phase B capability
  [`Wiki requirements collection`](../phase-b-business-architecture/capabilities/wiki-product-line.md).
- [`traceability.md`](traceability.md) — worked example traces
  (Phase A goal → Phase B / D dimension → Phase F experiment →
  Phase H promotion).
- [`adr/`](adr/) — Requirements-Management-scoped ADRs (rare;
  one is opened only when the *process* changes).

## Forward references

- [`../phase-a-architecture-vision/goals.md`](../phase-a-architecture-vision/goals.md)
  — top-level requirements (TTS / PTS / EB / Architect-velocity).
- [`../phase-b-business-architecture/capabilities/`](../phase-b-business-architecture/capabilities/)
  — capability trajectories (Phase B requirements live here).
- [`../phase-d-technology-architecture/services/`](../phase-d-technology-architecture/services/)
  — service trajectories (Phase D requirements live here).
- [`../phase-f-migration-planning/experiments/`](../phase-f-migration-planning/experiments/)
  — active and recently-closed experiment specs (closure attempts).
- [`../phase-h-architecture-change-management/`](../phase-h-architecture-change-management/)
  — promotion mechanics (Level 2 → new Level 1 with deletion of
  prior level).
