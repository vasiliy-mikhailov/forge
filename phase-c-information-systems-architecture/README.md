# Phase C — Information Systems Architecture

## Application Architecture (the labs)

- [`application-architecture/components.md`](application-architecture/components.md)
  — table of forge's four application components and which Phase B
  capabilities each realises.
- [`application-architecture/<component>/`](application-architecture/)
  — one folder per component (lab), each with its own
  AGENTS.md / SPEC / Dockerfile / docker-compose / docs / tests.

The four components today: `wiki-compiler`, `wiki-bench`,
`wiki-ingest`, `rl-2048`.

## Data Architecture

- [`data-architecture/data-sets.md`](data-architecture/data-sets.md)
  — the per-product `raw.json` + skill-v2 wiki shape + bench
  artefact + retrieval-index data sets.
- [`data-architecture/`](data-architecture/) — schemas / additional
  per-set detail (when populated).

## ADRs

- [`adr/`](adr/) — Phase C scoped ADRs (cross-component data
  decisions; per-component ADRs live inside that component's
  folder).
