# Architecture repository

How forge's architecture artefacts are organized on disk, and the
conventions that keep them findable.

This file does double duty:

- It captures the **forge-specific layout** (Phase A-H folder
  convention, AGENTS.md / CLAUDE.md symlink, lab template, where
  ADRs live, on-disk vs git-tree split).
- It maps that layout to **canonical TOGAF Architecture
  Repository components** so a reader who knows TOGAF can find
  the corresponding artefacts in forge.

## Top-level: TOGAF Phase folders

The forge repo's top level is structured by TOGAF ADM phase plus
two cross-cutting folders:

- [`../`](../) — Phase Preliminary (this folder).
- [`../phase-requirements-management/`](../phase-requirements-management/)
  — continuous Requirements Management (center of the ADM).
- [`../phase-a-architecture-vision/`](../phase-a-architecture-vision/)
  through
  [`../phase-h-architecture-change-management/`](../phase-h-architecture-change-management/)
  — the eight ADM phases.

Each phase folder carries its own README + topical files (one file
per TOGAF entity — capability, service, principle, etc.) plus an
optional `adr/` subfolder for that phase's ADRs.

## Mapping to canonical TOGAF Architecture Repository

TOGAF defines **six repository components**. Each maps to a
location in forge:

| TOGAF component               | Where it lives in forge                                                                                                            |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| **Architecture Metamodel**    | This folder (`phase-preliminary/`) — the framework tailoring + repository conventions + method are the metamodel.                  |
| **Architecture Capability**   | [`architecture-team.md`](architecture-team.md) — who does architecture work (one architect of record).                            |
| **Architecture Landscape**    | The per-phase folders themselves describe the as-is landscape: Phase B capabilities, Phase C application components (labs), Phase D services with current Level 1. Per-lab `STATE-OF-THE-LAB.md` is the per-component view. |
| **Standards Information Base** (SIB) | Dockerfile pins (per lab), `forge/.env.example`, `phase-c-…/wiki-compiler/configs/models.yml` (vLLM model registry), `forge/common.mk`. No single file today; cross-link as needed. |
| **Reference Library**         | [`../phase-g-implementation-governance/lab-AGENTS-template.md`](../phase-g-implementation-governance/lab-AGENTS-template.md), `forge/common.mk`, `phase-c-…/wiki-bench/.agents/skills/openhands-sdk-orchestration.md`. The reusable patterns labs copy from. |
| **Governance Log**            | The per-phase `adr/` folders, taken together, are the governance log. We do not consolidate them into a single file — per-phase scope is more useful at this size. |

Forge does not adopt the rest of TOGAF's repository ceremony
(Foundation Architectures, Continuum hierarchy with Industry /
Common Systems / Organization-Specific tiers, formal SIB
classification scheme). These are headcount-scaling concerns that
do not earn their keep at single-architect scale — see
[`framework-tailoring.md`](framework-tailoring.md) for the full
list of skipped TOGAF concepts.

## Application Architecture: labs

Phase C contains an `application-architecture/` subfolder; inside
it are the four labs (application components):
`wiki-compiler/`, `wiki-bench/`, `wiki-ingest/`, `rl-2048/`. Each
lab carries its own:

- `AGENTS.md` — Phase A-H scoped to that lab (template at
  [`../phase-g-implementation-governance/lab-AGENTS-template.md`](../phase-g-implementation-governance/lab-AGENTS-template.md)).
- `Dockerfile`, `docker-compose.yml`, `Makefile` — runtime
  artefacts.
- `SPEC.md` — the lab's specification.
- `tests/` — per-lab smoke + regression tests.
- `docs/adr/` or `adr/` — lab-scoped ADRs (both layouts are legal).

## AGENTS.md / CLAUDE.md convention

Every directory that needs agent-context carries `AGENTS.md` as
the canonical file plus `CLAUDE.md` as a symlink pointing at it.
This way every popular agent tool (Claude Code, Codex CLI, Cowork)
finds the same content under whichever name it looks for.

The convention was unified on 2026-04-27. Forge root used to
invert it (CLAUDE.md as the file, AGENTS.md as the symlink); the
current state is `AGENTS.md` is the file at every location, with
`CLAUDE.md` → `AGENTS.md` everywhere.

## Per-lab AGENTS.md must follow the canonical template

The TOGAF phase structure is meant to *permeate*, not just live at
the top. Every lab's `AGENTS.md` uses the canonical Phase A-H
headers (lab-scoped content; same header text). Source of truth
for the template:
[`../phase-g-implementation-governance/lab-AGENTS-template.md`](../phase-g-implementation-governance/lab-AGENTS-template.md).

## Where ADRs live

ADRs are scoped to the phase whose layer the decision changes:

- **Forge-level ADRs** in `forge/phase-<x>/adr/NNNN-*.md`.
  Numbering is monotonic across all forge phases (the existing
  0001-0009 series). One file per decision; the file is the
  durable record.
- **Lab-scoped ADRs** in `<lab>/docs/adr/NNNN-*.md` or
  `<lab>/adr/NNNN-*.md` — both layouts are legal. Numbering is
  per lab.
- **Per-phase indexing in lab AGENTS.md.** Each lab's AGENTS.md
  has an `**ADRs (Phase X scope).**` block under each Phase
  section, listing the lab's ADRs that apply at that phase.

There is no `forge/docs/adr/` — that path is *historical*. Any
older doc that references it is stale.

## Storage layout (data, not code)

Code artefacts live in the git tree under the layout above. Data
artefacts (model weights, transcripts, bench runs, mlruns) live
under `${STORAGE_ROOT}` on disk, by convention
`/mnt/steam/forge/`:

- `${STORAGE_ROOT}/shared/models/` — HF model cache, shared
  across labs.
- `${STORAGE_ROOT}/labs/<lab>/...` — per-lab data
  (`vault/`, `sources/`, `checkpoints/`, `mlruns/`, etc.).

Storage layout is independent of repo layout. The `labs/<lab>/`
convention on disk predates the Phase C move in the git tree, and
on-disk paths under STORAGE_ROOT keep the older flat layout. This
is intentional — moving on-disk paths invalidates running
containers, while moving git paths only requires a doc update.

## Cross-references

- [`framework-tailoring.md`](framework-tailoring.md) — what
  TOGAF concepts forge adopts, what it skips (the full list,
  including the headcount-scaling ones).
- [`architecture-team.md`](architecture-team.md) — who edits
  this repository (the Architecture Capability).
- [`../phase-g-implementation-governance/governance.md`](../phase-g-implementation-governance/governance.md)
  — operational rules that live at Phase G (do/don't lists).
- [`../phase-g-implementation-governance/lab-AGENTS-template.md`](../phase-g-implementation-governance/lab-AGENTS-template.md)
  — the canonical per-lab Phase A-H template (Reference Library
  artefact).


## Motivation chain

Per [P7](architecture-principles.md):

- **Driver**: TOGAF Architecture Repository needs a forge-
  specific layout (where does each TOGAF metamodel component
  live in this monorepo).
- **Goal**: Architect-velocity (no path-hunting).
- **Outcome**: TOGAF component → forge path table.
- **Capability realised**: Architecture knowledge management.
- **Function**: Map-TOGAF-Repository-to-forge-paths.
- **Element**: this file.
