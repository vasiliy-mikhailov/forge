# ADR 0014 — ArchiMate 4 vocabulary across all phases

**Phase.** Preliminary (architecture method extension).

**Status.** Accepted.

**Date.** 2026-04-30.

**Normative reference.** ArchiMate® 4 Specification (The Open
Group, 2026), kept locally for offline lookup at
a local PDF kept at `phase-preliminary/adr/archimate-4-spec.pdf` (gitignored — Open Group spec is "Evaluation Copy, not for redistribution"; download from https://publications.opengroup.org/standards/archimate).

## Context

Forge organises its docs by TOGAF ADM phases (Preliminary, A–H,
plus continuous Requirements Management). TOGAF gives us *phase
scaffolding*; it does not give us a typed vocabulary of elements
and relationships. Three concrete losses follow:

- "operations stack" / "capability stack" / "stack" appear with
  three different table shapes across `phase-b/`. A reader
  cannot tell whether a row in one table is the same type as a
  row in another.
- "Actor", "agent", "role", "hat", "session" have all been used
  for the same concept (an LLM session that exercises
  responsibility on the architect's behalf). The agents/ →
  roles/ rename was a partial fix.
- The trajectory model — Level 1 (today) → Level 2 (target),
  delete on promotion — is hand-rolled prose that exactly
  matches ArchiMate's Implementation & Migration domain
  (**Plateau** + **Work Package** + **Deliverable**). We've
  been re-inventing those names.

The current
[`framework-tailoring.md`](../framework-tailoring.md) declares:

> ArchiMate vocabulary inside Phase D. When describing Technology
> Architecture we distinguish *services* (a behavior exposed by
> tech) from *components* (the artefact realising the service).

That scope was conservative. Three recent process regressions
have traced back to vocabulary slip — naming the same thing
differently in two phases and losing track that they were the
same. The cost is real, the fix is a typed vocabulary.

ArchiMate 4 (released 2025-2026) restructures the language
relative to the v3 most readers know. Two changes matter for
forge:

1. **Common Domain.** Role, Collaboration, Path, Service,
   Process, Function, Event, Grouping, Location are now
   *cross-domain* — not Business-specific. There is no
   "Business Role" or "Application Service" as a separate
   element type; there is just **Role** and **Service**, which
   can be assigned to actors / components / nodes from any of
   the Strategy / Business / Application / Technology /
   Implementation domains. This collapses much of the v3
   per-layer duplication.
2. **Implementation & Migration is reduced to three elements**
   — Work Package, Deliverable, Plateau. The v3 *Gap* element
   is gone. A "trajectory" between two Plateaus is implicit;
   a Work Package realizes the new Plateau.

Both changes simplify what forge has to adopt.

## Decision

**Forge adopts ArchiMate 4 as the modeling vocabulary across
all phases, at term level. We do not produce ArchiMate diagrams.**

Specifically:

1. **Use ArchiMate 4 element type names for elements forge
   describes.** Where a forge file names a thing ("the role",
   "the capability", "the lab", "the Level 2 state"), it uses
   the v4 ArchiMate term: **Role**, **Capability**,
   **Application Component**, **Plateau**.
2. **Cross-reference table** lives at
   [`archimate-vocabulary.md`](../archimate-vocabulary.md). Every
   existing forge concept maps to at most one ArchiMate 4
   element type (sometimes none — see the *Skip* list there).
   New concepts must either map to an ArchiMate 4 element or be
   justified as forge-specific.
3. **Domain scoping per phase.** Each TOGAF phase folder
   primarily uses ArchiMate elements from one or two domains:

   | TOGAF phase                          | ArchiMate 4 domain(s) primarily used                     |
   |--------------------------------------|-----------------------------------------------------------|
   | Phase A — Architecture Vision        | **Motivation** (Stakeholder, Driver, Goal, Principle)    |
   | Phase B — Business Architecture      | **Strategy** (Capability, Resource, Value Stream) + **Business** (Business Actor, Product) + **Common** (Role, Function, Service) |
   | Phase C — Information Systems        | **Application** (Application Component, Data Object) + **Common** (Service, Function) |
   | Phase D — Technology                 | **Technology** (Node, System Software, Communication Network) + **Common** (Service) + **Physical** (Equipment, Facility) |
   | Phase E/F — Opportunities/Migration  | **Implementation & Migration** (Work Package, Deliverable, Plateau) |
   | Phase G — Implementation Governance  | (no new elements; references)                             |
   | Phase H — Architecture Change        | **Implementation & Migration** (Plateaus, Work Packages, Deliverables) |
   | Requirements Management              | **Motivation** (Requirement as the headline)              |

   Cross-domain references are normal: a Capability (Strategy)
   is realized by a Function (Common) which is assigned to a
   Role (Common) and an Application Component (Application). The
   phase folder still owns the elements; cross-domain relations
   cite across folders by path.

4. **Relationship vocabulary** — adopted explicitly, named in
   prose:

   - **Structural** — Aggregation, Composition, Assignment,
     Realization.
   - **Dependency** — Serving, Access, Influence, Association.
   - **Dynamic** — Triggering, Flow.
   - **Other** — Specialization.
   - **Junctions** — And, Or.

   When a forge file describes a relationship, it names the
   ArchiMate term explicitly ("Wiki PM role *is assigned to*
   the Wiki-requirements-collection function, which *realizes*
   the Develop-wiki-product-line capability") rather than prose
   like "is responsible for" / "drives" / "owns". This is the
   load-bearing change — forge gets typed verbs.

5. **Trajectory model = Plateau + Work Package + Deliverable,
   made explicit.** The
   [`architecture-method.md`](../architecture-method.md)
   trajectory rule maps to ArchiMate 4 thus:

   - **Level 1** (today's stable state of a capability /
     service quality dimension) = the current **Plateau**.
   - **Level 2** (next planned state) = the target **Plateau**.
   - **Phase F experiment** that closes the gap = a **Work
     Package**.
   - **The artefacts the experiment produces** (a new image, a
     new prompt, a new ADR) = **Deliverables**, which realize
     the target Plateau.
   - **Promotion** = the moment Level 2 becomes the new Level 1;
     the prior Plateau description is *deleted from docs* per
     the existing forge method. ArchiMate does not prescribe
     deletion — that is a forge-specific rule on top of the v4
     vocabulary.

   Note: ArchiMate 4 has no **Gap** element. The "trajectory"
   between two Plateaus is implicit in the existence of both
   plus a Work Package connecting them. Forge keeps "trajectory"
   as informal prose ("the throughput trajectory") because it's
   shorter than "the gap between Level 1 and Level 2 plateaus
   for the throughput dimension."

6. **Domain alignment for forge's existing element types
   (worked):**

   | forge concept                       | ArchiMate 4 element                | Domain               |
   |-------------------------------------|-------------------------------------|----------------------|
   | Architect of record (the human)     | Business Actor                      | Business             |
   | Cowork / Claude session             | Business Actor                      | Business             |
   | Wiki PM, source-author, etc.        | Role                                | Common               |
   | Wiki requirements collection        | Function                            | Common               |
   | Compile lecture into source.md      | Function                            | Common               |
   | LLM inference at `inference.mikhailov.tech` | Service                     | Common               |
   | Develop wiki product line           | Capability                          | Strategy             |
   | wiki-bench, wiki-ingest, wiki-compiler | Application Component            | Application          |
   | vLLM, faster-whisper, caddy         | System Software                     | Technology           |
   | Blackwell GPU, RTX 5090             | Device                              | Technology           |
   | mikhailov.tech (the host)           | Node                                | Technology           |
   | raw.json                            | Data Object                         | Application          |
   | source.md, concept.md, corpus-observations.md | Business Object         | Business             |
   | Kurpatov Wiki, Tarasov Wiki         | Product                             | Business (composite) |
   | Wiki product line                   | Grouping                            | Common (composite)   |
   | Phase A goals (TTS / PTS / EB / Architect-velocity) | Goal                | Motivation           |
   | Phase A drivers                     | Driver                              | Motivation           |
   | Phase A stakeholders                | Stakeholder                         | Motivation           |
   | architecture-principles.md          | Principle                           | Motivation           |
   | catalog.md row (R-NN)               | Requirement                         | Motivation           |
   | Level 1 / Level 2 (any dimension)   | Plateau                             | Implementation & Migration |
   | Phase F experiment (e.g. K1)        | Work Package                        | Implementation & Migration |
   | Experiment outputs (image, ADR, prompt) | Deliverable                     | Implementation & Migration |

   The full table with prose definitions per row lives in
   [`archimate-vocabulary.md`](../archimate-vocabulary.md).

7. **What this is NOT.**

   Forge does not start producing ArchiMate **diagrams** as
   deliverables. The
   [`framework-tailoring.md`](../framework-tailoring.md)
   "Deliberately skipped" list rejects diagrams ("Pictures
   bit-rot faster than prose at this scale"). This ADR adopts
   the *vocabulary*, not the visual notation. ArchiMate-aware
   tooling (Archi, Sparx EA) remains optional and is not
   required for any forge artefact.

   Forge does not adopt ArchiMate viewpoints / views as a
   mandatory deliverable mechanism either — the per-phase
   folder structure already serves that purpose.

8. **What this lets us drop.**

   Several locally-invented terms become forbidden in *new*
   artefacts (existing artefacts transition over time as they're
   touched):

   - "operations stack" / "capability stack" — use
     **Capability Map** (rows = Capabilities; columns =
     Functions / Application Components that realize them).
   - "agent" as an org-unit — use ArchiMate **Business Actor**
     (the LLM session) and **Role** (what the session plays).
   - "trajectory" as a noun for an architectural element — keep
     as informal prose only; the typed pair is two **Plateaus**
     with a **Work Package**.
   - "stack" used loosely for grouping — use ArchiMate
     **Grouping** when we mean "elements that belong together
     by some criterion."

## Consequences

**Positive.**

- Cross-phase references stop being prose and start being typed
  with verbs from a finite list. When a Phase B file says "this
  capability is *realized by* the wiki-bench Application
  Component, which is *assigned to* the Compile-lecture
  function", a reader who knows ArchiMate immediately knows the
  relationship type and what cross-checks make sense.
- Trajectory model gets a published mapping. New contributors
  who know ArchiMate read forge's hand-rolled L1/L2 prose and
  recognise it as Plateau + Work Package + Deliverable.
- Vocabulary collisions become detectable. A grep for "stack"
  or "agent" against new artefacts becomes a defect signal.
- Common Domain unification (v4 over v3) means there is one
  **Role** type and one **Service** type across all domains —
  forge's existing roles/ folder maps cleanly without a
  "Business Role / Application Role" split.

**Negative — accepted.**

- More vocabulary surface. ArchiMate 4 has ~40 element types
  and ~10 relationship types. The vocabulary doc lists only the
  subset forge actually uses. That subset is still larger than
  the current ad-hoc set, but the cross-reference doc gives one
  definition per name in one place.
- Documentation churn during transition. Files using
  "operations stack" / "agent" need updating as they're
  touched. Not a big-bang rewrite — the next edit conforms.
- ArchiMate purists may flinch at our partial adoption (no
  diagrams, no formal viewpoints, no certified tools). The
  framework-tailoring rationale (single architect, prose over
  pictures) holds.

**Out of scope.**

- ArchiMate diagrams.
- ArchiMate Exchange Format / model-as-XML. Forge artefacts
  stay markdown.
- Mandatory full coverage on existing files. A file that is
  currently informal prose stays informal until it's touched;
  the next edit must conform.

## Currently realised

- This ADR.
- [`archimate-vocabulary.md`](../archimate-vocabulary.md) (new)
  — the cross-reference table mapping every existing forge
  concept to its ArchiMate 4 element type, plus the relationship
  vocabulary subset forge uses, plus the metamodel chains forge
  relies on most often.
- [`framework-tailoring.md`](../framework-tailoring.md) updated:
  the "ArchiMate vocabulary inside Phase D" line is broadened to
  "ArchiMate 4 vocabulary across all phases, per ADR 0014."

Application across the rest of the repo is incremental — files
already using vague vocabulary keep their content but get
ArchiMate-tagged the next time they're meaningfully edited.

## References

- ArchiMate® 4 Specification (The Open Group, 2026) — local
  copy at a local PDF kept at `phase-preliminary/adr/archimate-4-spec.pdf` (gitignored — Open Group spec is "Evaluation Copy, not for redistribution"; download from https://publications.opengroup.org/standards/archimate), §§ 4
  (Common Domain), 5 (Relationships and Junctions), 6
  (Motivation Domain), 7 (Strategy Domain), 8 (Business
  Domain), 9 (Application Domain), 10 (Technology Domain), 12
  (Implementation and Migration Domain).
- [`framework-tailoring.md`](../framework-tailoring.md) — what
  forge adopts from TOGAF + ArchiMate, what it skips.
- [`architecture-method.md`](../architecture-method.md) — the
  trajectory model this ADR maps to ArchiMate 4 Plateau + Work
  Package + Deliverable.
- [ADR 0013](0013-md-as-source-code-tdd.md) — sibling extension
  (md is source code; TDD applies). Together with this ADR,
  forge has both *what to write* (ArchiMate 4 vocabulary) and
  *how to verify it* (md TDD).
