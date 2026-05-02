# Stakeholders

- **Architect of record** — one person (the repo owner). Sole driver
  of trajectory changes, sole reviewer, today the only consumer of
  every output.
- **Future operator** — the architect's future self, who will inherit
  these docs, debug failures, and extend the platform. Most of what
  is written here is for them.
- **End users (wiki readers)** — formalised as 5 reader-segment
  personas filling the
  [Wiki Customer role](../phase-b-business-architecture/roles/wiki-customer.md)
  per [ADR 0016](../phase-preliminary/adr/0016-wiki-customers-as-roles.md):
  - [entry-level-student](../phase-b-business-architecture/roles/customers/entry-level-student.md) — linear reader, builds from zero.
  - [working-psychologist](../phase-b-business-architecture/roles/customers/working-psychologist.md) — index-and-skim for clinical techniques.
  - [lay-curious-reader](../phase-b-business-architecture/roles/customers/lay-curious-reader.md) — course-as-entertainment.
  - [academic-researcher](../phase-b-business-architecture/roles/customers/academic-researcher.md) — cross-references against literature.
  - [time-poor-reader](../phase-b-business-architecture/roles/customers/time-poor-reader.md) — 5-10 min cap; maximum density.

  Each persona produces a per-lecture pain ledger (under
  `phase-b-business-architecture/products/kurpatov-wiki/customer-pains/`);
  the Wiki PM cross-tabulates per
  [`wiki-customer-interview.md`](../phase-requirements-management/wiki-customer-interview.md)
  CI-1..7 cycle. Practical-Time-Saved is now measurable per
  segment, not just in aggregate.


## Motivation chain

Per [P7](../phase-preliminary/architecture-principles.md) +
[ADR 0016](../phase-preliminary/adr/0016-wiki-customers-as-roles.md):

- **Driver**: without typed stakeholders, the Wiki PM emits
  R-NN on architect intuition rather than on segment-specific
  reader pain (audit-2026-05-01p F1.b).
- **Goal**: TTS at per-segment granularity (Phase A).
- **Outcome**: 5 customer personas formalised; Wiki PM runs
  CI-1..7 cycle against them; per-persona pain ledgers feed
  R-NN emission.
- **Measurement source**: n/a — declarative: stakeholder roster (5 customer personas formalised in roles/customers/; abstract Wiki Customer in roles/wiki-customer.md)
- **Capability realised**: Develop wiki product line
  ([develop-wiki-product-line.md](../phase-b-business-architecture/capabilities/develop-wiki-product-line.md)).
- **Function**: Catalogue-Stakeholders-and-Concerns.
- **Element**: this file.
