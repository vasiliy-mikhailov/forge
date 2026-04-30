# Phase 0 — Preliminary

The Preliminary Phase precedes Phase A in TOGAF ADM. It is *not*
about the architecture content; it is about the **architecture
capability itself** — how this enterprise (forge) does architecture
at all, before any specific Architecture Vision is set.

In classic TOGAF, the Preliminary Phase establishes:

1. **Scope and stakeholders of the architecture capability.**
2. **Architecture team and governance** — who drives architecture
   work and how decisions are taken.
3. **Architecture principles** — the meta-rules every architecture
   decision must obey.
4. **Architecture frameworks selected and tailored** — which parts
   of TOGAF / ArchiMate we use, which we skip.
5. **Architecture method** — the operating model for moving the
   architecture forward (in our case, the Level 1 / Level 2
   trajectory model).
6. **Architecture repository** — where the artifacts live and
   how they're organized.

Subsequent ADM iterations (Phase A → H → A → …) skip Preliminary
and reuse the capability it set up. forge revisits Preliminary
only when one of these meta-decisions changes — e.g. if a second
architect joined, governance would change and Preliminary would be
re-opened.

## Layout

- [`framework-tailoring.md`](framework-tailoring.md) — what TOGAF
  + ArchiMate 4 vocabulary forge adopts, what it deliberately skips
  (no formal Architecture Definition Document; no certification;
  no ArchiMate diagrams).
- [`archimate-language.md`](archimate-language.md) — description of
  ArchiMate 4 itself (domains, element types, relationship verbs).
  The forge-internal reference for the modeling language.
- [`archimate-vocabulary.md`](archimate-vocabulary.md) — mapping
  every existing forge concept to one ArchiMate 4 element type;
  the four canonical metamodel chains forge relies on.
- [`architecture-team.md`](architecture-team.md) — single architect
  of record. No committee, no formal review process. Future-
  operator and end-users are stakeholders (Phase A), not part of
  the architecture team.
- [`architecture-principles.md`](architecture-principles.md) — the
  four meta-principles every architecture decision in forge obeys:
  single architect, capability trajectories, containers-only,
  single-server deployment.
- [`architecture-method.md`](architecture-method.md) — the Level 1
  / Level 2 trajectory model and the "delete on promotion, git is
  the archive" convention. This is the *method declaration*; Phase
  H operates the method.
- [`architecture-repository.md`](architecture-repository.md) — the
  TOGAF Phase A-H folder layout, AGENTS.md / CLAUDE.md symlink
  convention, the per-lab AGENTS.md template requirement, where
  ADRs live (per phase, per lab).
- [`adr/`](adr/) — Preliminary-scope ADRs (rare; one is opened
  only when a meta-decision above changes).

## Forward to Phase A

Once Preliminary is set, the first Architecture Vision is drafted
in [`../phase-a-architecture-vision/`](../phase-a-architecture-vision/).
That phase scopes one ADM iteration's *content* (vision,
stakeholders for that iteration, drivers, goals); Preliminary
defines the *capability* that produces those phases.
