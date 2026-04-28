# Architecture repository

How forge's architecture artefacts are organized on disk, and the
conventions that keep them findable.

## Top-level: TOGAF Phase folders

The forge repo's top level is structured by TOGAF ADM phase:

- [`../phase-preliminary/`](../) (this folder) — meta-capability.
- [`../phase-a-architecture-vision/`](../phase-a-architecture-vision/)
- [`../phase-b-business-architecture/`](../phase-b-business-architecture/)
- [`../phase-c-information-systems-architecture/`](../phase-c-information-systems-architecture/)
- [`../phase-d-technology-architecture/`](../phase-d-technology-architecture/)
- [`../phase-e-opportunities-and-solutions/`](../phase-e-opportunities-and-solutions/)
- [`../phase-f-migration-planning/`](../phase-f-migration-planning/)
- [`../phase-g-implementation-governance/`](../phase-g-implementation-governance/)
- [`../phase-h-architecture-change-management/`](../phase-h-architecture-change-management/)

Each phase folder carries its own README + topical files (one file
per TOGAF entity — capability, service, principle, etc.) plus an
optional `adr/` subfolder for that phase's ADRs.

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
- `docs/adr/` (legacy) or `adr/` (newer) — lab-scoped ADRs.

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
- **Lab-scoped ADRs** in `<lab>/docs/adr/NNNN-*.md` (legacy) or
  `<lab>/adr/NNNN-*.md` (newer flatter layout). Numbering is per
  lab.
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

- [`framework-tailoring.md`](framework-tailoring.md) — what we
  adopt, what we skip.
- [`architecture-team.md`](architecture-team.md) — who edits this
  repository.
- [`../phase-g-implementation-governance/governance.md`](../phase-g-implementation-governance/governance.md)
  — operational rules that live at Phase G (do/don't lists).
- [`../phase-g-implementation-governance/lab-AGENTS-template.md`](../phase-g-implementation-governance/lab-AGENTS-template.md)
  — the canonical per-lab Phase A-H template.
