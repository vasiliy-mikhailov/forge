# psi -- subsidiary

| | |
|---|---|
| Subsidiary | course-wiki |
| Repo (private, auth-gated) | `git@github.com:vasiliy-mikhailov/course-wiki.git` |
| Category | private content tenant |
| Architect of record | shared with forge (single architect) |

URL above is permitted on forge-public per [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md).
Operational details (capabilities, products, services,
content) live inside the auth-gated repo per ADR 0030 §2 and
the daughter's own G3.1b regime (which inherits from
[ADR 0018](../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md)).

## What lives where

- Capabilities, products (kurpatov-wiki, tarasov-wiki),
  org-units: in course-wiki at
  `phase-b-business-architecture/` (auth-gated).
- Content (lecture transcripts, compiled wikis, metadata,
  prompts, skills): in course-wiki at `content/` and the
  preserved top-level dirs (auth-gated).
- Lab participation in forge mutex: forge schedules the
  generic `wiki-ingest`/`wiki-compiler`/`wiki-bench` labs
  per `phase-g-implementation-governance/policies/`;
  course-wiki's content flows through them as the tenant
  payload.
- Audit reports about course-wiki: forge writes them at
  `../../phase-h-architecture-change-management/subsidiary-audits/psi-YYYY-MM-DD.md`,
  with operational identifiers aliased per ADR 0030.

## Integration history

- 2026-05-10: course-wiki repo created and populated in a
  single architect-of-record session. No separate
  integration brief: course-wiki was empty, all migration
  sources were accessible from a single authority. The
  jarvis-style request/response thread is replaced by this
  catalog entry plus the
  [course-wiki forge-integration README](https://github.com/vasiliy-mikhailov/course-wiki/blob/main/phase-h-architecture-change-management/forge-integration/README.md).
- 2026-05-10: kurpatov-wiki-raw + kurpatov-wiki-wiki
  contents absorbed into course-wiki; legacy repos may be
  archived.
- 2026-05-10: forge phase-b kurpatov/tarasov files
  migrated to course-wiki; this catalog entry lands.

## Related

- [ADR 0018](../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md) -- content-side privacy boundary (the rule that kurpatov + tarasov content stays in the daughter).
- [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md) -- name-side privacy boundary; this file is permitted by ADR 0030.
- [omega.md](omega.md) -- sibling subsidiary (jarvis, the embodied-control daughter).
