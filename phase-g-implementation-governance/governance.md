# Implementation governance

The *operational* rules — what to do and not do day-to-day in the
working tree. The meta-decisions about how forge does architecture
at all (architecture team, framework choice, principles, method,
repository layout) live one layer above in
[`../phase-preliminary/`](../phase-preliminary/) and are not
re-stated here.

## Forge-wide do / don't

- **All work runs in containers.** Source of truth:
  [`policies/containers.md`](policies/containers.md). This is the
  enforcement of the [`P3 — containers-only`](../phase-preliminary/architecture-principles.md)
  principle.
- **AGENTS.md per location** is canonical at every directory.
  CLAUDE.md is a symlink → AGENTS.md at every location. Convention
  established in
  [`../phase-preliminary/architecture-repository.md`](../phase-preliminary/architecture-repository.md).
- **Single source of truth per location.** If AGENTS.md (or
  AGENTS.md plus its phase-folder pages) conflicts with code, fix
  one or the other but do not let drift persist.
- **ADR for irreversible decisions.** If on-disk data format
  changes, the framework choice changes, or the network topology
  changes — add `phase-<x>/adr/NNNN-*.md` (or
  `phase-c-…/application-architecture/<lab>/docs/adr/NNNN-*.md`
  for lab-scoped) where NNNN is the next free number.

## Per-lab AGENTS.md must follow the canonical template

Every lab's `AGENTS.md` follows the canonical Phase A-H template
in [`lab-AGENTS-template.md`](lab-AGENTS-template.md). The
template itself is a Preliminary-phase artefact (it defines how
labs participate in the architecture); maintenance of the
template lives here under Phase G.

Labs that don't yet have AGENTS.md must add one when their next
substantive change lands. Until then, the forge-level AGENTS.md is
the authoritative reference for those labs.

## Lab-local governance

Lab-specific do / don't lists live in each lab's AGENTS.md
Phase G section, not here. Examples:

- "GPU 0 hosts compiler OR rl-2048 not both" — lives in
  `wiki-compiler/AGENTS.md` § Phase G.
- "Always `docker stop --time 10` before `docker rm -f` for
  CUDA-active containers" — lives in `wiki-compiler/AGENTS.md`
  § Phase G.
- "Bench artefacts go to `${STORAGE_ROOT}/labs/wiki-bench/...`" —
  lives in `wiki-bench/AGENTS.md` § Phase G.

## Cross-references

- [`policies/`](policies/) — forge-wide policy documents (today:
  containers).
- [`operations.md`](operations.md) — runbook material for the
  architect (GPU recovery, smoke-test contract, backup priorities).
- [`lab-AGENTS-template.md`](lab-AGENTS-template.md) — the
  canonical per-lab Phase A-H template.
- [`adr/`](adr/) — Phase G scoped ADRs (governance / process
  decisions).
- [`../phase-preliminary/`](../phase-preliminary/) — the
  meta-decisions this phase enforces.
