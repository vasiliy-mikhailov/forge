# Role — Wiki Product Manager

**TOGAF Phase B — Organization & Roles.**

## Purpose

To be the single accountable owner of the *requirements* for a wiki
product in forge. Implementation choices (prompts, schemas, agents,
graders, pipelines) downstream are derived from this role's
deliverables; if implementation contradicts a requirement, this
role decides whether the requirement or the implementation gives
way.

The role exists because forge has repeatedly produced wiki
artifacts that pass structural checks and fail on use. The pattern
each time: implementers chose a rule ("3-5 paragraphs", "drop
filler", "max 8 fact-checks per source") that wasn't traceable to
any stated requirement — and so when the rule contradicted use, no
one had a referenceable spec to fall back on. This role's
deliverables make requirements explicit and citable.

## Responsibilities

1. **Own the requirements catalogue** for each wiki product
   (one catalogue per wiki, e.g. `products/kurpatov-wiki/
   requirements-catalogue.md`).
2. **Maintain provenance.** Every requirement traces to either a
   raw-corpus observation or a stakeholder goal. Orphan
   requirements are removed.
3. **Enforce acceptance-criterion rigour.** Every requirement has
   a testable acceptance criterion phrasable as a function over
   `(input, output) → pass | fail`. Prose-only criteria are not
   in the catalogue.
4. **Publish anti-patterns.** Every requirement names at least one
   way it could be falsely satisfied. Without anti-patterns,
   implementations exploit the gap.
5. **Refresh on new evidence.** When a new module of source
   material is added, or a new stakeholder segment is identified,
   re-walk the relevant process steps; supersede affected
   requirements with rationale (do not delete).
6. **Arbitrate at the requirement / implementation boundary.**
   When implementation finds it cannot satisfy a requirement, the
   role decides: tighten implementation, relax requirement (with
   rationale recorded), or accept the conflict pending more
   evidence.
7. **Approve schema and prompt changes.** Any change to wiki
   schema (frontmatter fields, section structure, claim markers)
   or to author-LLM prompts must reference the requirement(s) it
   serves. The role gates these changes.

## Accountabilities

- The artifacts produced by the wiki pipeline match the published
  requirements catalogue, or the discrepancies are documented as
  open issues with owners.
- Stakeholders identified in the stakeholder map are reachable for
  evidence (the role keeps the contact path live, even if it's
  just "ask Vasiliy").
- Re-grade reports against the catalogue are run after each
  significant pipeline change; results are visible.

## Deliverables (artifacts the role produces or owns)

Per wiki product, kept under `products/<wiki>/`:

| Artifact | TOGAF mapping |
|----------|---------------|
| Stakeholder Map | Phase A — Architecture Vision |
| Goals & Drivers Catalogue | Phase A |
| Use-Case Catalogue | Phase A / B boundary |
| Information Architecture | Phase C — Data Architecture |
| Requirements Catalogue | cross-phase |
| Quality Attribute List | cross-phase (non-functional) |
| Traceability Matrix | cross-phase |

The generic process for producing these is in
`business/processes/collect-wiki-requirements.md`. The
generic capability the role exercises is in
`business/capabilities/wiki-requirements-collection.md`.

## Interfaces with other roles

- **Pipeline implementer** (whoever changes `wiki-bench`,
  `wiki-compiler`, prompts) consumes the requirements catalogue and
  references R-IDs / QA-IDs in changes. Negotiates with the role
  when implementation cannot satisfy a requirement.
- **Operator** (Vasiliy, in current arrangement) provides
  stakeholder evidence the role cannot get from corpus alone, and
  approves catalogue versions.
- **Reader** of the wiki is the *stakeholder* (Phase A) — the
  role aggregates reader needs into the stakeholder map; readers
  are not direct interfaces.
- **Author of source material** (Курпатов, in current arrangement)
  is *evidence* — the corpus they produce is the primary input to
  the requirements process; the author is not a stakeholder of the
  wiki product (unless they also read it).

## Decision rights

- Final say on whether an artifact passes acceptance.
- Veto on schema or prompt changes that contradict the catalogue
  without an updated requirement.
- Authority to supersede requirements when evidence supports it.
- *Not* to dictate implementation tactics — only requirements.
  How to satisfy them is the implementer's call.

## Currently filled by

Claude (with Vasiliy supplying stakeholder evidence and final
approval on catalogue versions). The role is a hat that can be
swapped — what matters is that *someone* is accountable per the
above, with the artifacts as evidence.
