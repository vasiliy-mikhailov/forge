# ADR 0001 — flat monorepo, no submodules

## Status
Accepted (2026-04-19). **Layout amended by [ADR 0007](../../phase-g-implementation-governance/adr/0007-labs-restructure-self-contained-caddy.md) (2026-04-25)**: top-level subsystem folders moved under `labs/<lab>/`. Core decision (single repo, no submodules) preserved.

## Context
I have several subsystems (caddy, mlflow, rl-2048, kurpatov-wiki) running on
a single physical machine and coupled by a shared `.env`, a shared docker
network `proxy-net`, and a shared `STORAGE_ROOT`. I work on them solo and
want "restore from scratch" to take minutes.

Options considered:

1. One repo, flat structure (one folder per service).
2. Git submodules: a root repo linking to per-service repos.
3. Separate repos with no tie — only a README in one of them pointing at
   the others.

## Decision
Flat monorepo. Everything in one git repository in sibling folders:

```
forge/
├── caddy/
├── mlflow/
├── rl-2048/
├── kurpatov-wiki/
├── docs/
├── Makefile
├── common.mk
└── .env / .env.example
```

## Consequences
- Plus: atomic edits — a Dockerfile change for a service and the matching
  `.env` tweak land in one commit.
- Plus: disaster recovery is a single `git clone`.
- Plus: one CLAUDE.md for all agents.
- Minus: commit history is mixed — to see "what I did only in
  kurpatov-wiki" I have to filter by path.
- Minus: if a subsystem grows into a standalone product, I'll have to do a
  `git subtree split`. Accepted for now.

## Rejected
- **Submodules.** I'm a solo developer; isolation value is near-zero and
  the cost (constantly forgetting `git submodule update`, painful clones)
  is high.
- **Separate repos.** Atomicity of cross-service contract changes
  (`.env`, compose, network) is lost.


## Motivation

Per [P7](../architecture-principles.md) — backfit:

- **Driver**: forge tree shape decides every navigation +
  search cost; a flat monorepo (one top-level for all phases)
  keeps the architect's loop fast.
- **Goal**: Architect-velocity.
- **Outcome**: every Phase has its own top-level subdirectory;
  no nested "src/" wrapper.
- **Measurement source**: audit-predicate: P3 (single-repo flat layout)
