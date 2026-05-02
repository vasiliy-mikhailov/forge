# ArchiMate 4 vocabulary used in forge

The cross-reference table mapping forge concepts to ArchiMate 4
element types and the relationship verbs forge uses. Decided in
[ADR 0014](adr/0014-archimate-across-all-layers.md). New to ArchiMate? Read
[`archimate-language.md`](archimate-language.md) first — that's the
language description (domains, elements, relationship verbs). This
file is the *forge → ArchiMate* mapping; that file is *what
ArchiMate is*.

Spec reference (offline copy):
a local PDF kept at `adr/archimate-4-spec.pdf` (gitignored — Open Group spec is "Evaluation Copy, not for redistribution"; download from https://publications.opengroup.org/standards/archimate).

## How to read this doc

Two sections:

1. **Element type table** — every named thing in forge with the
   ArchiMate 4 element it maps to, the domain that element lives
   in, and a one-line note on why the mapping is right.
2. **Relationship verbs** — the subset of ArchiMate 4
   relationships forge uses, with the prose form to write into
   docs ("Wiki PM is *assigned to* …"). When forge prose
   describes a connection between two elements, it should use
   one of these verbs.

A third **metamodel chains** section shows the most common
forge-specific compositions.

## Element type table

Per [ADR 0014](adr/0014-archimate-across-all-layers.md). The
"Domain" column reflects ArchiMate 4 (note Common Domain hosts
Role / Service / Process / Function / Event / Grouping / Location
— they are no longer Business-specific).

### Motivation domain

| forge concept                                                 | ArchiMate 4 element | Notes |
|---------------------------------------------------------------|---------------------|-------|
| Architect of record                                           | Stakeholder         | The single human stakeholder per `phase-a/stakeholders.md`. (Also a Business Actor when filling roles — see Business domain.) |
| Future operator                                               | Stakeholder         | Same as above; treated as a real stakeholder (Phase A). |
| End users                                                     | Stakeholder         | TBD per Phase A; identical with the architect today. |
| Phase A drivers (`drivers.md` entries)                        | Driver              | What raises forge's goals. |
| Phase A goals — TTS / PTS / EB / Architect-velocity           | Goal                | Top-level outcomes the architect tracks. |
| `architecture-principles.md` four principles                  | Principle           | Single-architect, capability-trajectories, containers-only, single-server. Constraints on every decision. |
| `phase-requirements-management/catalog.md` row (R-NN)         | Requirement         | Each row is a quality-dimension trajectory between two Plateaus, expressed as a Requirement. |
| Assessment of a metric gap surfaced in Phase E                | Assessment          | Used informally in audits today; would become a typed `phase-h/audit-*.md` element. |

### Strategy domain

| forge concept                                                 | ArchiMate 4 element | Notes |
|---------------------------------------------------------------|---------------------|-------|
| `phase-b/capabilities/forge-level.md` rows (R&D, Service Operation, Product Delivery, Architecture KM) | Capability | The four forge-level capabilities. |
| `phase-b/capabilities/develop-wiki-product-line.md`           | Capability          | The wiki-line-specific capability that decomposes R&D + Product Delivery + Architecture KM. |
| `phase-b/capabilities/service-operation.md`                   | Capability          | Same Service Operation row from forge-level, deep-dive page. |

ArchiMate 4 also defines **Resource**, **Value Stream**, and
**Course of Action** in this domain — none currently used
explicitly in forge; if/when they become useful (e.g.
Value Streams for the wiki product line), they'd land here too.

### Business domain

| forge concept                                                 | ArchiMate 4 element | Notes |
|---------------------------------------------------------------|---------------------|-------|
| Architect of record (the human, when filling a role)          | Business Actor      | Same individual, different ArchiMate aspect: Stakeholder (Motivation) when reasoning about goals; Business Actor (Business) when assigned to a Role. |
| Cowork desktop session / Claude Code / Codex CLI session      | Business Actor      | LLM agents that fill forge's Roles. Per ADR 0014 the term "agent" is used informally; the typed term is Business Actor. |
| `data/sources/<...>.md`, `data/concepts/<...>.md`             | Business Object     | The wiki content readers consume. |
| `phase-b/products/kurpatov-wiki/corpus-observations.md`       | Business Object     | The Wiki PM's working evidence file. |
| Kurpatov Wiki, Tarasov Wiki                                   | Product             | Composite element bundling the wiki output (Business Objects) + the underlying Service. |
| Wiki product line                                             | Grouping            | Composite element; aggregates Kurpatov + Tarasov Products. (Common domain composite, used here on the Business side.) |

### Common domain (Role / Service / Process / Function — cross-domain)

| forge concept                                                 | ArchiMate 4 element | Notes |
|---------------------------------------------------------------|---------------------|-------|
| Wiki PM (the role definition in `phase-b/roles/wiki-pm.md`)   | Role                | A Role is the position or purpose an Actor performs (v4 §4.1.1). |
| (future) wiki-bench developer role                            | Role                | Pending persona file. |
| Source-author / concept-curator pre-ADR-0013                  | Role                | Was an external agent role; now subsumed into the wiki-bench Application Component. |
| Wiki requirements collection                                  | Function            | Behavior grouped by required skills and resources (v4 §4.2.3). Realizes the Develop wiki product line Capability. |
| Compile lecture into source.md                                | Function            | The behavior the wiki-bench Application Component is assigned to. |
| Audio → text transcription                                    | Function            | The behavior wiki-ingest is assigned to. |
| LLM inference at `inference.mikhailov.tech`                   | Service             | Externally observable behavior of the wiki-compiler component. (v4 §4.2.1.) |
| `make smoke` / dispatcher                                     | Service             | Forge top-level orchestration service. |
| K1 v2 source-by-source progression                            | Process             | Sequence-of-actions in time, one source after another (v4 §4.2.2). |
| `tests/smoke.md` running-and-checking                         | Process             | Verifier process triggered by `make smoke`. |

### Application domain

| forge concept                                                 | ArchiMate 4 element | Notes |
|---------------------------------------------------------------|---------------------|-------|
| `phase-c/.../wiki-bench/` lab                                 | Application Component | Realizes the Compile-lecture Function and the Cross-source-dedup Function. |
| `phase-c/.../wiki-compiler/` lab                              | Application Component | Realizes the LLM-inference Service. |
| `phase-c/.../wiki-ingest/` lab                                | Application Component | Realizes the Transcription Function. |
| `phase-c/.../rl-2048/` lab                                    | Application Component | Realizes the rl-2048 capability stack. |
| `raw.json`                                                    | Data Object         | Per-source whisper segments. |
| `source.md` / `concept.md` (as files, not as content)         | Data Object         | The artefacts on disk; the *content* is a Business Object. |
| `phase-requirements-management/catalog.md`                    | Data Object         | The requirements catalog as a file (the rows are Requirements). |
| `bench_grade.py`                                              | Application Component | Embedded in wiki-bench; could be its own component. |

### Technology domain

| forge concept                                                 | ArchiMate 4 element | Notes |
|---------------------------------------------------------------|---------------------|-------|
| `mikhailov.tech` host machine                                 | Node                | Single-server forge per architecture-principle 4. |
| Blackwell RTX PRO 6000                                        | Device              | A node component. |
| GeForce RTX 5090                                              | Device              | A node component. |
| HDD pool / `${STORAGE_ROOT}` (`/mnt/steam/forge`)             | Device (Storage)    | Local data-store device. |
| vLLM (0.19.1, cu130)                                          | System Software     | The active LLM serving stack. |
| faster-whisper                                                | System Software     | The active transcription stack. |
| caddy 2                                                       | System Software     | Reverse proxy + TLS. |
| Docker + Compose                                              | System Software     | Container runtime. |
| `proxy-net` Docker network                                    | Communication Network | Single internal network. |
| HTTPS endpoint at `inference.mikhailov.tech`                  | Technology Interface| The interface the wiki-compiler exposes for the LLM Service. |

### Physical sub-domain (used inside Technology)

| forge concept                                                 | ArchiMate 4 element | Notes |
|---------------------------------------------------------------|---------------------|-------|
| The home-lab room                                             | Facility            | Where mikhailov.tech runs. |

### Implementation & Migration domain

| forge concept                                                 | ArchiMate 4 element | Notes |
|---------------------------------------------------------------|---------------------|-------|
| Level 1 (current state of any quality dimension)              | Plateau             | Stable architecture state per `architecture-method.md`. |
| Level 2 (next planned state)                                  | Plateau             | Target Plateau. |
| Phase F experiment (`phase-f/experiments/<id>.md`)            | Work Package        | Time-and-resource-bounded effort that closes a gap between Plateaus. |
| Experiment outputs (new image, new prompt, new ADR, canonical commit) | Deliverable | Realizes (parts of) the target Plateau. |
| Phase H "promotion" event                                     | (forge-specific)    | The moment Level 2 becomes the new Level 1; the prior Plateau description is *deleted from docs* (forge rule on top of ArchiMate 4). |

ArchiMate 4 has no Gap element; the v3 Gap is implicit in the
existence of two Plateaus + a Work Package connecting them.


## Relationship verbs

ArchiMate 4 § 5. Forge prose uses these verbs (italicised) when
describing a connection between two elements; vague verbs ("is
responsible for", "drives", "owns") are forbidden in new prose
unless they map to one of these.

| ArchiMate verb                | Prose form                            | Source-target pattern (typical)                      |
|-------------------------------|---------------------------------------|------------------------------------------------------|
| **Aggregation**               | "X *aggregates* Y" / "Y is *aggregated by* X" | Composite (Product, Plateau, Grouping) ← part      |
| **Composition**               | "X *is composed of* Y"                | Whole ← exclusive part                               |
| **Assignment**                | "X *is assigned to* Y"                | Active structure (Actor / Role / Component / Node) → Behavior (Function / Process / Service) |
| **Realization**               | "X *realizes* Y"                      | Concrete → abstract: Function realizes Capability; Component realizes Service; Deliverable realizes Plateau |
| **Serving**                   | "X *serves* Y" / "X *is used by* Y"   | Provider behavior → consumer                         |
| **Access**                    | "X *accesses* Y"                      | Behavior → passive (Function accesses Data Object)   |
| **Influence**                 | "X *influences* Y"                    | Motivation only: Driver → Goal; Goal → Requirement   |
| **Association**               | "X *is associated with* Y"            | Catch-all for relations that don't fit the others    |
| **Triggering**                | "X *triggers* Y"                      | Dynamic, time-ordered: Event → Process; Process → Process |
| **Flow**                      | "X *flows to* Y"                      | Information / data / energy passing                  |
| **Specialization**            | "X *is a specialization of* Y"        | Sub-type → super-type                                |

## Metamodel chains forge relies on

A few canonical chains forge uses repeatedly. Name them when
writing related prose to make the typing visible.

### Wiki-PM chain (how the role realizes a capability)

```
Architect of record (Business Actor)
   │ assigned to
   ▼
Wiki PM (Role)
   │ assigned to
   ▼
Wiki requirements collection (Function)
   │ realizes
   ▼
Develop wiki product line / Requirement traceability (Capability)
   │ contributes to closing
   ▼
R-B-wiki-req-collection (Requirement)
   │ influenced by
   ▼
Architect-velocity (Goal)
   │ influenced by
   ▼
(Phase A driver — implicit in Vasiliy's value model)
```

### Pipeline chain (how a lab realizes a capability)

```
wiki-bench (Application Component)
   │ assigned to
   ▼
Compile lecture into source.md (Function)
   │ realizes
   ▼
Develop wiki product line / Voice preservation (Capability)
   │ accesses
   ▼
raw.json (Data Object)
```

### Migration chain (how an experiment moves a plateau)

```
G3 dense-Gemma experiment (Work Package)
   │ realizes
   ▼
G3 close-out artefacts (Deliverables: ADR, image, contract test)
   │ realizes
   ▼
"throughput Level 2" (Plateau)
   │ realizes (capability increment)
   ▼
Service Operation / throughput (Capability)
   │ closes
   ▼
R-B-svcop-thruput (Requirement)
```

### Stack alignment (how Phase B / Phase C / Phase D talk to each other)

```
Capability                          ← Strategy domain (Phase B)
   │ realized by
   ▼
Function                             ← Common domain
   │ assigned to
   ▼
Application Component                ← Application domain (Phase C)
   │ realized by
   ▼
System Software (e.g. vLLM)          ← Technology domain (Phase D)
   │ deployed on
   ▼
Node (mikhailov.tech)                ← Technology domain (Phase D)
```

When a forge file describes an alignment that crosses these
levels, it should name the ArchiMate verb and target type
explicitly. Vague phrasings like "the lab uses vLLM" become "the
wiki-compiler Application Component is realized by vLLM
(System Software) deployed on the mikhailov.tech Node."

## See also

- [ADR 0014](adr/0014-archimate-across-all-layers.md) — the
  decision that brought this vocabulary in.
- [`framework-tailoring.md`](framework-tailoring.md) — what
  forge adopts from TOGAF + ArchiMate, what it skips.
- ArchiMate® 4 Specification (offline copy at
  a local PDF kept at `adr/archimate-4-spec.pdf` (gitignored — Open Group spec is "Evaluation Copy, not for redistribution"; download from https://publications.opengroup.org/standards/archimate)),
  §§ 4-7 + 12 are the most relevant.


## Measurable motivation chain (OKRs)
Per [P7](architecture-principles.md):

- **Driver**: ADR 0014 adopted ArchiMate; the project needs
  a forge-typed vocabulary catalog (which spec elements are
  in scope, with examples).
- **Goal**: Audit reliability (P6, P14, P24 reference this).
- **Outcome**: typed elements catalogued; new artifact types
  inherit vocab discipline.
- **Measurement source**: n/a — declarative: ArchiMate 4 vocabulary catalog (typed-element reference; consumed by P14)
- **Capability realised**: Architecture knowledge management.
- **Function**: Hold-forge-typed-vocabulary.
- **Element**: this file.
