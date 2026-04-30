# Capability — Wiki Requirements Collection

**TOGAF Phase B — Business Capability.**

## Capability statement

The ability to derive a complete, traceable, testable set of
requirements for a wiki product from (a) the raw source material
the wiki will summarise, and (b) the goals of the audiences who
will read it — and to keep that set current as evidence accumulates.

## Owner

[Role — Wiki Product Manager](../roles/wiki-product-manager.md).

A capability without a named owning role is just a wish; this one
has a role with decision rights to enforce it.

## Inputs

The capability consumes:

- **Raw source corpus** of the wiki product — transcripts, PDFs,
  HTML, anything the wiki will be derived from. Used for both
  *substance* (what content exists) and *form* (what voice and
  structure the corpus has — drives anti-pattern identification).
- **Stakeholder evidence** — direct input from operators, prior
  wiki readers, analytics on how the wiki is used. In current
  forge arrangement this comes from Vasiliy.
- **Existing artifacts** of the wiki, when one is already in
  flight — frontmatter conventions, prompts, evals — these
  surface implicit requirements that haven't been written down.
- **Existing decision records** — the relevant `docs/adr/` entries
  that constrain what this wiki can or cannot be.

## Outputs

The capability produces a per-wiki collection under
`products/<wiki>/`:

| Output | Form |
|--------|------|
| Stakeholder Map | structured table |
| Goals & Drivers Catalogue | structured table |
| Use-Case Catalogue | numbered cases with steps |
| Information Architecture | entity model + relations |
| Requirements Catalogue | numbered R-IDs with provenance and acceptance criteria |
| Quality Attribute List | numbered QA-IDs with measures and targets |
| Traceability Matrix | requirement × stakeholder/goal/use-case grid |

Each output has a fixed shape so consumers (implementers, graders)
can write tooling against it. Output schemas are defined in the
process spec (`processes/collect-wiki-requirements.md`).

## Value provided

Three concrete failure modes go away:

1. **Implementation without spec.** Today, a prompt rule like
   "3-5 paragraphs of 100-200 words" can land with no requirement
   it serves; when it produces a long-TL;DR-shaped Лекция, no one
   can point to which requirement was violated. After this
   capability is in place, every implementation cites an R-ID;
   when output fails on use, the conversation is "did the
   requirement say the wrong thing, or did implementation fail
   to satisfy it?", not "whose intuition was wrong?"
2. **Quality dashboard lying.** Today, bench_grade can report
   "100% of sources have short Лекция" while a regex bug zeroes
   the measurement and the actual content is fine. After this
   capability, every measurement is tied to a QA-ID with a
   defined measure and target; a measure that disagrees with
   eye-read on real artifacts is a defect of the measure or the
   QA target, both of which get versioned and reviewed.
3. **Silent skips of work.** Today, deletions of pipeline steps
   (concept-curator, fact-check breadth) can ship as "speedup"
   because nothing measured the property the deleted step
   produced. After this capability, every property worth keeping
   is in the QA list; deleting a step that produced a QA-tracked
   property is visible immediately.

## Maturity criteria

The capability is at a given maturity level when these are true:

| Level | Criteria |
|-------|----------|
| **L0 — Not present** | Requirements live in heads or chat threads, not in artifacts. Implementation choices made by intuition. |
| **L1 — Catalogued** | Per-wiki Requirements Catalogue exists with R-IDs, even if some lack provenance or acceptance criteria. |
| **L2 — Traceable** | Every requirement traces to ≥ 1 use-case AND ≥ 1 evidence source (corpus observation or stakeholder goal). Orphans removed. |
| **L3 — Testable** | Every requirement has an acceptance criterion implementable as a function over `(input, output)`. |
| **L4 — Anti-patterned** | Every requirement names ≥ 1 anti-pattern. |
| **L5 — Enforced** | Implementation references R-IDs in code/prompt comments. Verifier runs acceptance criteria automatically. Catalogue updates trigger pipeline review. |

L5 is the target; the capability is useful at L1-L2 already.

## Dependencies on other capabilities

- **Corpus access** — without read access to the raw source
  material, the capability degenerates to "ask the operator and
  guess." Forge's existing kurpatov-wiki-raw repo + ingest
  pipeline satisfies this.
- **Stakeholder reachability** — at minimum, the operator must be
  reachable for evidence the corpus alone can't supply (e.g.
  *"do practising therapists actually want this wiki, or only
  students?"*).
- **Eval / measurement substrate** — without a way to run an
  acceptance criterion as code, the catalogue is aspirational.
  The wiki-bench pipeline supplies this.

## Anti-patterns for the capability itself

- **Catalogue as wish-list.** Requirements written without
  evidence ("the Лекция should be high-quality") that survive
  several reviews because no one challenges them — this is the
  capability operating at L1 dressed as L3.
- **Implementation owns the requirements.** When implementation
  decides what the requirement is by what's easy to build, the
  role has been informally captured. Symptom: every requirement
  exactly matches what the current implementation already does.
- **One big catalogue, no traceability.** A long list of
  requirements with no UC or stakeholder columns — looks
  comprehensive, can't be re-derived if a stakeholder changes.

## Currently at maturity level

L0 (start of the work that produces this section). Next milestone:
L2 for the kurpatov-wiki product, with the catalogue committed in
`products/kurpatov-wiki/`.
