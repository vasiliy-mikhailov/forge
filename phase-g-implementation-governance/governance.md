# Implementation governance

The rules that decide what lands in the working tree, who decides,
and the format every lab follows.

## Roles

- **Architect of record** — one person (the repo owner). All
  trajectory changes pass through them. No committee, no PR review
  automation beyond the AGENTS.md convention.

## Forge-wide rules

- **All work runs in containers.** Source of truth:
  [`policies/containers.md`](policies/containers.md).
- **AGENTS.md per lab** carries operational rules for that lab; the
  forge-level [`../AGENTS.md`](../AGENTS.md) carries cross-cutting
  rules.
- **Single source of truth per location.** AGENTS.md (or its
  symlinked CLAUDE.md) is the canonical doc at any folder; if it
  conflicts with code, fix one or the other but do not let drift
  persist.

## Per-lab AGENTS.md must follow the canonical template

The TOGAF ADM phase structure is meant to *permeate*, not just live
at the top. Every lab's `<lab>/AGENTS.md` must use the canonical
phase headers (Phase A through Phase H, classic TOGAF names — see
[`lab-AGENTS-template.md`](lab-AGENTS-template.md)), scoped to that
lab. The template is the source of truth for section ordering and
wording; copy from it when adding or editing a lab AGENTS.md.

**Symlink convention.** Each lab keeps `AGENTS.md` as the regular
file and `CLAUDE.md` as a symlink → `AGENTS.md`. Forge root inverts
the direction (`AGENTS.md` → `CLAUDE.md`) for historical reasons —
leave that as is.

**Coverage.** Labs that don't yet have AGENTS.md must add one when
their next substantive change lands. Until then, the forge-level
AGENTS.md is the authoritative reference for those labs.

## Cross-references

- [`policies/`](policies/) — forge-wide policies (containers, etc).
- [`operations.md`](operations.md) — runbook material for the
  architect.
- [`lab-AGENTS-template.md`](lab-AGENTS-template.md) — the canonical
  per-lab Phase A-H template.
- [`adr/`](adr/) — Phase G scoped ADRs (governance / process
  decisions).
