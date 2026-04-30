# ArchiMate 4 — language description

The modeling language forge adopted in
[ADR 0014](adr/0014-archimate-across-all-layers.md). This file is
the forge-internal description of what ArchiMate 4 *is*: its
structure, its element types, its relationship types. It is the
companion to [`archimate-vocabulary.md`](archimate-vocabulary.md)
(which maps existing forge concepts to ArchiMate 4 elements) and
to [`framework-tailoring.md`](framework-tailoring.md) (which says
which parts forge adopts and skips).

Source: ArchiMate® 4 Specification (The Open Group, 2026), kept
locally for offline lookup at `adr/archimate-4-spec.pdf`
(gitignored — Open Group spec is "Evaluation Copy. Not for
redistribution"; download from
<https://publications.opengroup.org/standards/archimate>). Every
section below cites the relevant spec section so a contributor
with access can dig deeper. Definitions in this file are in
forge's own words.

This file is a **digest**, not a translation of the spec. Where
the spec exhaustively enumerates every constraint, this file
records only what forge actually relies on. Elements forge does
not use today are simply absent from the tables below; per the
[architecture method's](architecture-method.md) delete-on-
promotion rule, the working tree reads as current truth, not as
a status log.

## What ArchiMate is

A modeling language for enterprise architecture, developed by The
Open Group. Two things matter for forge:

- A **fixed vocabulary** of element types (each with a precise
  definition) and relationship types (each with a precise
  semantics). When a forge file says "X realizes Y", that verb
  is one of 11 named relationships with a defined meaning, not
  prose.
- A **layered metamodel** organised by domains (Strategy,
  Business, Application, Technology, Motivation, Implementation
  & Migration, Common, Physical). Each domain has its own
  element types; cross-domain relations are explicit.

The language also defines a visual notation (boxes, arrows,
icons) and a viewpoint mechanism for producing diagrams. Forge
**adopts the vocabulary and skips the notation** — see
[`framework-tailoring.md`](framework-tailoring.md). The forge
artefacts are markdown; ArchiMate gives them typed names.

## Structural axes (spec §3)

Every element belongs to one *aspect*. The three aspects are:

- **Active structure** — entities that perform behavior (Actors,
  Components, Nodes, Roles).
- **Passive structure** — entities behavior acts on (Data
  Objects, Business Objects, Artifacts).
- **Behavior** — the activities themselves (Functions,
  Processes, Services, Events).

Plus three special-case aspects:

- **Motivation** — the *why* (Stakeholders, Drivers, Goals,
  Requirements). Spec §6.
- **Composite** — elements that aggregate other elements
  (Grouping, Location, Product, Plateau). Cross-aspect.
- **Implementation & Migration** — Work Package, Deliverable,
  Plateau (these have their own domain). Spec §12.

The three core aspects (active / passive / behavior) appear in
every domain that has core elements (Business, Application,
Technology). The **Common Domain** (spec §4) is the v4-specific
unification: Role, Service, Process, Function, Event,
Collaboration, Path, Grouping, Location are *cross-domain*
elements — they don't belong to Business or Application or
Technology individually. This is the major change from
ArchiMate 3 forge contributors should be aware of.

## Domains and their elements

**Tables list only the elements forge actually uses today.** Elements not listed are described in the spec; if forge starts using one, its row is added to the relevant table at that point. This matches the architecture-method.md rule that the working tree reads as current truth, not as a status log.

Listed in the order forge phases use them (Motivation first
because it drives Phase A; Strategy → Business → Application →
Technology because that's the layering; Implementation &
Migration last because it sits orthogonally).

### Common domain (spec §4)

Cross-domain elements — Role, Service, Process, Function, Event,
Collaboration, Path, Grouping, Location. These can be assigned
to / realized by elements in any of the Strategy / Business /
Application / Technology domains.

| Element       | One-line definition (forge phrasing)                                                                    | Spec ref |
|---------------|----------------------------------------------------------------------------------------------------------|----------|
| **Role**          | The position or purpose an active structure element (Business Actor, Application Component, Node, etc.) plays in performing behavior. *Forge example: Wiki PM.* | §4.1.1 |
| **Service**       | An explicitly defined behavior an active structure element provides to its environment, accessible through interfaces. *Forge example: LLM inference service exposed by wiki-compiler.* | §4.2.1 |
| **Process**       | A sequence of behaviors that achieves a specific result; ordered "flow" of activities. *Forge example: per-source progression in K1 v2.* | §4.2.2 |
| **Function**      | A collection of behavior grouped by required skills / resources / knowledge — *not* by sequence. Realizes Capabilities. *Forge example: Compile-lecture-into-source.md.* | §4.2.3 |
| **Event**         | An instantaneous occurrence (state change) that triggers / is triggered by behavior. *Forge example: "Pilot completed" triggering "Publish step".* | §4.2.4 |
| **Grouping**      | A composite element that aggregates concepts belonging together by some criterion. *Forge example: the Wiki product line aggregating Kurpatov + Tarasov Products.* | §4.3.1 |

### Motivation domain (spec §6)

The *why* layer. Reasons behind the architecture.

| Element       | One-line definition (forge phrasing)                                                                    | Spec ref |
|---------------|----------------------------------------------------------------------------------------------------------|----------|
| **Stakeholder** | An individual or group with a stake in the outcome of the architecture. *Forge example: architect of record, future operator.* | §6.3.1 |
| **Driver**      | An external or internal condition that motivates the organization to define its goals and implement changes. *Forge example: "AI tools should save human time on cognitive work".* | §6.3.2 |
| **Assessment**  | The result of analysis of the state of the enterprise with respect to a driver — surfaces strengths, weaknesses, opportunities, threats. *Forge example: a Phase H audit row.* | §6.3.3 |
| **Goal**        | A high-level statement of intent or direction for the enterprise. *Forge example: TTS, PTS, EB, Architect-velocity (Phase A).* | §6.4.1 |
| **Principle**   | A normative property of all systems in a given context. *Forge example: the four architecture-principles (single architect, capability trajectories, containers-only, single server).* | §6.4.3 |
| **Requirement** | A statement of need that must be realized by the architecture. *Forge example: each row in `phase-requirements-management/catalog.md`.* | §6.4.4 |

### Strategy domain (spec §7)

What the enterprise *can do*.

| Element       | One-line definition (forge phrasing)                                                                    | Spec ref |
|---------------|----------------------------------------------------------------------------------------------------------|----------|
| **Capability**     | An ability the enterprise possesses; *what* the enterprise can do, independent of how it implements it. *Forge example: Develop wiki product line; Service operation.* | §7.3.1 |

A Capability is *realized by* one or more Functions. A Function
is *assigned to* a Role and / or an Application Component / Node.
This chain — Capability ← Function ← Role / Component — is the
load-bearing one for forge (see §[Metamodel chains forge relies
on](#metamodel-chains-forge-relies-on)).

### Business domain (spec §8)

The Business domain in v4 is intentionally thin — most behavior /
service / process / function / role concepts moved to Common
Domain.

| Element       | One-line definition (forge phrasing)                                                                    | Spec ref |
|---------------|----------------------------------------------------------------------------------------------------------|----------|
| **Business Actor**     | An organizational entity (person, org unit, organization) capable of performing behavior. *Forge example: architect of record (the human); a Cowork session (an LLM agent).* | §8.2.1 |
| **Business Object**    | A passive element of business significance — concept / information / fact relevant to the business domain. *Forge example: source.md / concept.md content; corpus-observations.md.* | §8.3.1 |
| **Product**            | A coherent collection of Services and Business Objects, accompanied by a Contract / set of agreements offered to customers. *Forge example: Kurpatov Wiki, Tarasov Wiki.* | §8.4.1 |

### Application domain (spec §9)

The application / software layer.

| Element       | One-line definition (forge phrasing)                                                                    | Spec ref |
|---------------|----------------------------------------------------------------------------------------------------------|----------|
| **Application Component** | An encapsulated software unit with well-defined functionality and interfaces. *Forge example: wiki-bench, wiki-compiler, wiki-ingest.* | §9.2.1 |
| **Data Object**           | Data structured for automated processing. *Forge example: raw.json, the source.md / concept.md files (as files, not as content), catalog.md.* | §9.3.1 |

### Technology domain (spec §10)

The infrastructure / hardware layer. Includes the Physical
sub-domain (Equipment, Facility, Distribution Network, Material).

| Element       | One-line definition (forge phrasing)                                                                    | Spec ref |
|---------------|----------------------------------------------------------------------------------------------------------|----------|
| **Node**            | A computational or physical resource that hosts, manipulates, or interacts with other resources. *Forge example: the mikhailov.tech host.* | §10.2.1 |
| **Technology Interface** | A point of access where Technology Services are made available. *Forge example: HTTPS endpoint at inference.mikhailov.tech.* | §10.2.2 |
| **Device**          | A physical IT resource. *Forge example: the Blackwell GPU; the RTX 5090.* | §10.2.3 |
| **System Software** | Software environment supporting application and other software components. *Forge example: vLLM, faster-whisper, caddy, Docker.* | §10.2.4 |
| **Facility**        | A physical structure providing the environment for hosting equipment. *Forge example: the home-lab room.* | §10.2.6 |
| **Communication Network** | A set of structures and behaviors that connect computer systems. *Forge example: the proxy-net Docker network.* | §10.2.7 |

### Implementation & Migration domain (spec §12)

Three elements only in v4. The v3 *Gap* element is gone — a
trajectory between two Plateaus is implicit.

| Element       | One-line definition (forge phrasing)                                                                    | Spec ref |
|---------------|----------------------------------------------------------------------------------------------------------|----------|
| **Work Package** | A series of actions identified to achieve specific results within time / resource constraints. Has a start and an end. *Forge example: a Phase F experiment (e.g. K1 v2).* | §12.2.1 |
| **Deliverable**  | A result of a Work Package. *Forge example: the new Docker image, the new ADR, the canonical commit produced by an experiment.* | §12.2.2 |
| **Plateau**      | A relatively stable state of the architecture during a limited period of time. *Forge example: Level 1 (today) and Level 2 (next planned) for a quality-dimension trajectory.* | §12.2.3 |

A Plateau may aggregate any Strategy or Core domain element. A
Deliverable may realize a Plateau (or any Strategy / Core
element). A Role may be assigned to a Work Package (e.g. a
project manager). Motivation elements (Goals, Requirements) can
be related to specific Plateaus — useful when requirements differ
between current and target architectures.

## Relationships and Junctions (spec §5)

The 11 typed verbs forge prose uses. Spec § 5.1–5.4 gives full
semantics; this is forge's compressed reference.

| Class       | Verb               | Forge prose form                          | Source-target pattern |
|-------------|--------------------|--------------------------------------------|------------------------|
| Structural  | **Aggregation**     | "X *aggregates* Y" / "Y is *part of* X"    | Composite (Product, Plateau, Grouping) ← part |
| Structural  | **Composition**     | "X *is composed of* Y"                     | Whole ← exclusive part (stronger than Aggregation) |
| Structural  | **Assignment**      | "X *is assigned to* Y"                     | Active structure → Behavior (or Role / Function); Actor → Role |
| Structural  | **Realization**     | "X *realizes* Y"                           | Concrete → abstract (Function → Capability; Component → Service; Deliverable → Plateau) |
| Dependency  | **Serving**         | "X *serves* Y" / "Y *is served by* X"      | Provider behavior → consumer |
| Dependency  | **Access**          | "X *accesses* Y"                           | Behavior → passive (Function accesses Data Object) |
| Dependency  | **Influence**       | "X *influences* Y"                         | Motivation only (Driver → Goal; Goal → Requirement) |
| Dependency  | **Association**     | "X *is associated with* Y"                 | Catch-all when none of the above fits |
| Dynamic     | **Triggering**      | "X *triggers* Y"                           | Time-ordered: Event → Process; Process → Process |
| Dynamic     | **Flow**            | "X *flows to* Y"                           | Information / data / material passing |
| Other       | **Specialization**  | "X *is a specialization of* Y"             | Sub-type → super-type |

**Junctions** (§5.5): an *And-junction* connects multiple
relationships of the same type that all hold; an *Or-junction*
connects relationships where at least one holds. Used in
diagrams; forge prose uses "and" / "or" naturally.

**Multiplicity** (§5.6): every relationship has a multiplicity
(0..1, 0..*, 1..1, 1..*) which forge does not write explicitly
in prose unless ambiguous.

**Derivation** (§5.8): some relationships imply others (e.g.
Composition → Aggregation; Realization → Specialization). Forge
does not rely on derivation in prose.

## Stakeholders, Views, Viewpoints (spec §13)

A **viewpoint** is a specification of conventions for selecting,
classifying, and presenting concepts of a model — for a specific
audience addressing specific concerns. A **view** is the
application of a viewpoint to produce a representation. ArchiMate
defines an extensible set of example viewpoints (Capability Map,
Business Process View, Application Cooperation View, etc.).

Forge does not adopt viewpoints / views as a deliverable
mechanism. Each TOGAF phase folder serves the same purpose
prose-style; ADR 0014 explicitly skips diagrams and viewpoints.
The mechanism is documented here so a future contributor knows
the option exists if forge ever needs structured per-stakeholder
views.

## Language Customization (spec §14)

ArchiMate 4 allows specialization of element types and addition
of attributes. Forge does not customize the language today —
all element types used are stock. If a future need arises (e.g.
"GPU Capacity" as a specialised Resource), the customization is
declared in the same archimate-vocabulary.md table by adding a
row with a "specialization of" column.


## What this file is NOT

- **Not a substitute for the spec.** When in doubt, read the
  spec section cited in the row. This file is forge-specific
  digest, not a translation.
- **Not exhaustive.** It enumerates the elements and
  relationships forge uses or might use; lower-level concepts
  (e.g. detailed semantics of Composition vs Aggregation) live
  in the spec.
- **Not a tutorial.** ArchiMate has rich training material and
  certification courses; a contributor who needs to learn the
  language from scratch should use those resources, then come
  back here for forge's specific usage.

## Cross-references

- [ADR 0014](adr/0014-archimate-across-all-layers.md) — the
  decision to adopt ArchiMate 4 across all phases.
- [`archimate-vocabulary.md`](archimate-vocabulary.md) — every
  forge concept's mapping to one of the elements above.
- [`framework-tailoring.md`](framework-tailoring.md) — what
  forge adopts and skips; pointer back to this file.
- [`architecture-method.md`](architecture-method.md) — the
  trajectory model expressed in ArchiMate 4 terms (Plateaus +
  Work Packages + Deliverables).
