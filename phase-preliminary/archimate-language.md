# ArchiMate 4 — language description

**Transitive coverage** (per ADR 0013 dec 9 + ADR 0017): this file is a forge-independent ArchiMate 4 language reference (spec §6 + §7 + §8 + §9). Motivation chain inherited from [`archimate-vocabulary.md`](archimate-vocabulary.md) (the consumer-facing typed-element catalog that every Phase artifact cites). Measurement source on the parent: `n/a — declarative`.

A reference for the ArchiMate® 4 modeling language as standardised
by The Open Group. This file describes the language itself —
domains, element types, relationship types, structural rules —
independent of how any specific project applies it. It is intended
to be a portable digest a reader can rely on without knowing the
project context.

For how this project specifically maps its concepts to ArchiMate 4
elements, see the companion file
[`archimate-vocabulary.md`](archimate-vocabulary.md). For the
decision to adopt ArchiMate 4, see
[ADR 0014](adr/0014-archimate-across-all-layers.md). For the full
normative text, refer to the ArchiMate 4 Specification (The Open
Group, 2026); section numbers (e.g. §4.1.1) cited below point into
that document. Definitions in this file are paraphrased; the
spec is the source of truth.

## Contents

- [What ArchiMate is](#what-archimate-is)
- [Language structure](#language-structure)
- [Common Domain](#common-domain)
- [Motivation Domain](#motivation-domain)
- [Strategy Domain](#strategy-domain)
- [Business Domain](#business-domain)
- [Application Domain](#application-domain)
- [Technology Domain](#technology-domain)
- [Implementation & Migration Domain](#implementation--migration-domain)
- [Relationships and Junctions](#relationships-and-junctions)
- [Stakeholders, Views, and Viewpoints](#stakeholders-views-and-viewpoints)
- [Language Customization](#language-customization)

## What ArchiMate is

ArchiMate is an Enterprise Architecture modeling language
maintained as an Open Group standard. It provides a **fixed
vocabulary** of element types and relationship types used to
describe an organisation's architecture across multiple concerns
— motivations, strategy, business, applications, technology,
implementation — plus a **graphical notation** for diagrams. The
language sits *alongside* TOGAF: TOGAF provides the development
method and phase scaffolding; ArchiMate provides the typed terms
that fill those phases.

Two halves of the language matter:

- **Vocabulary.** Element types (Capability, Application
  Component, Plateau, …) and relationship types (Realization,
  Assignment, Influence, …) with precise semantics. Two
  artefacts that name the same thing using ArchiMate vocabulary
  refer to the same element.
- **Notation.** Boxes, arrows, icons, colours that render the
  vocabulary visually. Optional — adopting the vocabulary
  without the notation is conformant.

ArchiMate 4 (2026) restructures the language relative to v3:
common cross-domain elements (Role, Service, Process, Function,
Event, Collaboration, Path, Grouping, Location) move into a
single **Common Domain**, and the Implementation & Migration
domain reduces to three elements (Work Package, Deliverable,
Plateau — v3's *Gap* element is retired).

## Language structure

Spec §3.

### Aspects

Every element belongs to one *aspect*. The three core aspects
are:

- **Active Structure** — entities that *perform* behaviour.
  Examples: Business Actor, Application Component, Node, Role.
- **Passive Structure** — entities that behaviour *acts on*.
  Examples: Business Object, Data Object, Artifact.
- **Behavior** — the activities themselves. Examples: Service,
  Process, Function, Event.

Three further aspects sit alongside the core three:

- **Motivation** — the *why*. Stakeholder, Driver, Goal,
  Requirement, etc.
- **Composite** — elements that aggregate concepts from multiple
  aspects. Grouping, Location, Product, Plateau.
- **Implementation & Migration** — Work Package, Deliverable,
  Plateau (this aspect overlaps Composite for Plateau).

### Domains

Elements are organised into seven **domains** (called *layers*
in ArchiMate 3):

| Domain                              | Spec § | Purpose                                                                                                              |
|-------------------------------------|--------|-----------------------------------------------------------------------------------------------------------------------|
| **Common**                          | §4     | Cross-domain elements (Role, Service, Process, Function, etc.) that can be used in Strategy, Business, Application, or Technology. |
| **Motivation**                      | §6     | The *why* — Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Meaning, Value.                  |
| **Strategy**                        | §7     | What the enterprise *can do* (Capabilities, Resources) and *plans to do* (Courses of Action, Value Streams).         |
| **Business**                        | §8     | The business layer — actors, interfaces, business objects, products.                                                |
| **Application**                     | §9     | Application components, interfaces, data objects.                                                                    |
| **Technology**                      | §10    | Infrastructure — nodes, devices, system software, networks, plus a Physical sub-domain (Equipment, Facility, etc.). |
| **Implementation & Migration**     | §12    | Work Packages, Deliverables, Plateaus.                                                                                |

Cross-domain references are normal and the language defines them
explicitly (e.g. an Application Component may *realize* a
Capability — §11).

### Active / Passive / Behavior in core domains

Each of Business, Application, Technology has its own Active
Structure, Passive Structure, and Behavior elements *in addition
to* the cross-domain Common elements. So Application has both
**Application Component** (Active) and **Data Object** (Passive)
of its own, while reusing **Service**, **Process**, **Function**,
**Event** from Common.

## Common Domain

Spec §4. Elements in this domain are not tied to any single core
domain — they can apply to actors / components / nodes from any
of Strategy, Business, Application, or Technology.

### Active Structure

| Element            | Definition                                                                                                                                                    | Spec § |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Role**           | The position or purpose that an active structure element (Business Actor, Application Component, Node, Device, System Software, Equipment, Facility, or a Collaboration) has in performing specific behaviour. | §4.1.1 |
| **Collaboration**  | A (possibly temporary) collection of internal active structure elements that work together to perform collective behaviour.                                                                                     | §4.1.2 |
| **Path**           | A logical link between active structure elements through which they exchange information, data, energy, or material.                                                                                            | §4.1.3 |

### Behavior

| Element       | Definition                                                                                                                                                              | Spec § |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Service**   | An explicitly defined behaviour that an active structure element provides to its environment, accessible through interfaces. Externally observable.                       | §4.2.1 |
| **Process**   | A sequence of behaviours that achieves a specific result. Sequence- or flow-oriented.                                                                                    | §4.2.2 |
| **Function**  | A collection of behaviour grouped by required skills, resources, knowledge, etc. — *not* by sequence. Functions can realize Capabilities.                                | §4.2.3 |
| **Event**     | An instantaneous occurrence (e.g., state change) inside or outside the enterprise. Triggers or is triggered by other behaviour.                                          | §4.2.4 |

Process vs Function: a Process is *sequence-of-activities*; a
Function is *grouping-by-skill-or-resource*. The same set of
activities can be modelled both ways depending on the question
being asked.

### Composite

| Element     | Definition                                                                                                                                                                  | Spec § |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Grouping** | A composite element that aggregates a collection of concepts belonging together based on some common characteristic. Used for arbitrary groupings (e.g. ABBs/SBBs in TOGAF). | §4.3.1 |
| **Location** | A composite element representing a conceptual or physical place or position where concepts are located.                                                                     | §4.3.2 |

## Motivation Domain

Spec §6. The *why* layer. Captures the reasons behind the
architecture — who cares, what drives change, what goals exist,
what requirements follow.

### Stakeholders, Drivers, Assessments

| Element        | Definition                                                                                                                                                            | Spec § |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Stakeholder** | The perspective from which a Business Actor perceives the effects of the architecture. Has interests / concerns; sets and emphasises Goals.                            | §6.3.1 |
| **Driver**      | An external or internal condition that motivates an organisation to define its goals and implement changes. (Drivers associated with a Stakeholder are *concerns*.)   | §6.3.2 |
| **Assessment**  | The result of an analysis of the state of affairs of the enterprise with respect to some Driver. Surfaces strengths, weaknesses, opportunities, threats.              | §6.3.3 |

### Goals, Outcomes, Principles, Requirements

| Element        | Definition                                                                                                                                                                 | Spec § |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Goal**       | A high-level statement of intent, direction, or desired end state for an organisation and its stakeholders. Typically uses qualitative words ("increase", "improve").       | §6.4.1 |
| **Outcome**    | An end result, effect, or consequence of a state of affairs. Tangible, possibly quantitative, time-related. Distinguishes "what you get" from a Goal's "what you want."     | §6.4.2 |
| **Principle**  | A statement of intent defining a general property that applies to *any* system in a certain context. Broader and more abstract than a Requirement.                          | §6.4.3 |
| **Requirement** | A statement of need defining a property that applies to a *specific* system as described by the architecture. The "means" to realize Goals.                                 | §6.4.4 |

Principle vs Requirement: a Principle constrains *all* solutions
in a context ("Data should be stored only once"); a Requirement
constrains *one specific* system ("Use a single CRM system").

### Meaning and Value

| Element     | Definition                                                                                                                                                | Spec § |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Meaning** | The knowledge or expertise present in, or the interpretation given to, a concept in a particular context. Often used to describe Passive Structure elements. | §6.5.1 |
| **Value**   | The relative worth, utility, or importance of an element. May differ across stakeholders.                                                                  | §6.5.2 |

## Strategy Domain

Spec §7. What the enterprise *can do* and how it plans to do it.

### Structure

| Element     | Definition                                                                                                                              | Spec § |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Resource** | An asset (tangible or intangible) owned or controlled by an individual or organisation. Active structure on the Strategy layer.        | §7.2.1 |

### Behavior

| Element            | Definition                                                                                                                                                                   | Spec § |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Capability**     | An ability that an active structure element possesses. Describes *what* the enterprise can do, independent of *how* it implements it. Realized by Functions / Processes.       | §7.3.1 |
| **Value Stream**   | A sequence of value-creating stages an enterprise performs to provide value to its stakeholders. Each stage typically uses one or more Capabilities.                          | §7.3.2 |
| **Course of Action** | A plan or directional approach for configuring some unit of an enterprise's strategy. Differentiated, externally focused, and time-bounded.                                  | §7.3.3 |

Capability vs Function: Capability is *intentional and
implementation-independent*; Function is *current, day-to-day,
organisation-aligned*. A Capability can be realized by one or
more Functions.

## Business Domain

Spec §8. The business layer is intentionally thin in v4 — most
behavior / service / process / function / event concepts moved
to the Common Domain.

### Active Structure

| Element                | Definition                                                                                                                                              | Spec § |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Business Actor**     | An organisational entity (person, organisation, or organisational unit) capable of performing behaviour.                                                | §8.2.1 |
| **Business Interface** | A point of access where a Service is made available to the environment.                                                                                  | §8.2.2 |

### Passive Structure

| Element            | Definition                                                                                                                                                                          | Spec § |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Business Object** | A concept used within a particular business domain — a passive element of business significance. Represents information / facts that a process or function operates on.            | §8.3.1 |

### Composite

| Element    | Definition                                                                                                                                                                                                  | Spec § |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Product** | A coherent collection of Services, Business Objects, and / or Passive Structure elements, accompanied by a contract / set of agreements offered to internal or external customers as a whole.              | §8.4.1 |

## Application Domain

Spec §9. Software components, interfaces, data.

### Active Structure

| Element                       | Definition                                                                                                                                                | Spec § |
|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Application Component**     | An encapsulated unit of software with well-defined functionality and interfaces. Modular and replaceable.                                                  | §9.2.1 |
| **Application Interface**     | A point of access where Application Services are made available to a user, another application component, or a node.                                       | §9.2.2 |

### Passive Structure

| Element        | Definition                                                                                                                                                                  | Spec § |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Data Object** | Data structured for automated processing. The application-layer counterpart to a Business Object.                                                                          | §9.3.1 |

## Technology Domain

Spec §10. Infrastructure layer; includes a Physical sub-domain.

### Active Structure

| Element                  | Definition                                                                                                                                                                                                            | Spec § |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Node**                 | A computational or physical resource that hosts, manipulates, or interacts with other resources. Generic technology-domain active structure.                                                                          | §10.2.1 |
| **Technology Interface** | A point of access where Technology Services are made available.                                                                                                                                                       | §10.2.2 |
| **Device**               | A physical IT resource on which System Software and Artifacts may be stored or deployed. Specialisation of Node.                                                                                                      | §10.2.3 |
| **System Software**      | Software environment supporting application or other software components. Specialisation of Node. Examples: operating systems, database engines, application servers, container runtimes.                              | §10.2.4 |
| **Equipment**            | One or more physical machines, tools, or instruments that can create, use, store, move, or transform materials. Physical sub-domain.                                                                                   | §10.2.5 |
| **Facility**             | A physical structure or environment hosting Equipment or providing the location for technology. Physical sub-domain.                                                                                                    | §10.2.6 |
| **Communication Network** | A set of structures and behaviours that connects computer systems and devices for the exchange of data.                                                                                                              | §10.2.7 |
| **Distribution Network** | A physical network used to transport materials or energy. Physical sub-domain.                                                                                                                                         | §10.2.8 |

### Passive Structure

| Element        | Definition                                                                                                                                                          | Spec § |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Artifact**   | A piece of data used or produced in a software development or system operation context. The deployable / deployed counterpart of a Data Object on the technology layer. | §10.3.1 |
| **Material**   | A tangible physical material used or produced in a manufacturing process. Physical sub-domain.                                                                       | §10.3.2 |

## Implementation & Migration Domain

Spec §12. Three elements only in v4.

| Element           | Definition                                                                                                                                                              | Spec § |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| **Work Package**  | A series of actions identified and designed to achieve specific results within specified time and resource constraints. Has a start and an end. Used for projects, programs, sprints. | §12.2.1 |
| **Deliverable**   | A result of a Work Package. May be a report, document, software, physical product, organisational change, or implementation of (part of) an architecture.              | §12.2.2 |
| **Plateau**       | A relatively stable state of the architecture during a limited period of time. Used to model Baseline / Transition / Target architectures.                              | §12.2.3 |

A Plateau may aggregate any Strategy / Common / Business /
Application / Technology element. A Deliverable may realize
(parts of) a Plateau or any element of those domains. Motivation
elements (Goals, Requirements) can be related to specific
Plateaus — useful when requirements differ between current and
target architectures.

ArchiMate 4 has no *Gap* element; the v3 Gap is implicit in the
existence of two Plateaus connected by a Work Package.

## Relationships and Junctions

Spec §5. ArchiMate defines eleven typed relationship verbs plus
junctions, multiplicity, and derivation rules.

### Structural Relationships (§5.1)

| Relationship       | Spec §  | Source → Target pattern                                                                                                                  | Semantics                                                                                                            |
|--------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| **Aggregation**    | §5.1.1  | Composite ← part                                                                                                                          | A composite element conceptually contains other elements (parts can exist independently).                            |
| **Composition**    | §5.1.2  | Whole ← exclusive part                                                                                                                   | Stronger than Aggregation: parts cannot exist outside the whole.                                                     |
| **Assignment**     | §5.1.3  | Active Structure → Behavior (or Role / Function); Actor → Role; Role → Process / Function; Component → Function / Service.               | Allocates responsibility: who performs what.                                                                         |
| **Realization**    | §5.1.4  | Concrete → abstract (Function realizes Capability; Component realizes Service; Deliverable realizes Plateau; Requirement realizes Goal). | The source makes the target real.                                                                                    |

### Dependency Relationships (§5.2)

| Relationship    | Spec §  | Source → Target pattern                                                              | Semantics                                                                                                                  |
|-----------------|---------|---------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| **Serving**     | §5.2.1  | Provider behaviour / interface → consumer (active or behaviour).                      | The source provides functional value to the target.                                                                       |
| **Access**      | §5.2.2  | Behaviour → Passive Structure (Function / Process / Service accesses Object).         | A behaviour reads from / writes to / uses a passive element.                                                              |
| **Influence**   | §5.2.3  | Motivation → Motivation (Driver influences Goal; Goal influences Requirement).        | Positive or negative effect on motivation. Annotated with `+` / `−` or strength.                                          |
| **Association** | §5.2.4  | Any → any.                                                                            | Catch-all for relations that don't fit any other type. Generic linkage.                                                  |

### Dynamic Relationships (§5.3)

| Relationship    | Spec §  | Source → Target pattern                                       | Semantics                                                                                                |
|-----------------|---------|----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Triggering**  | §5.3.1  | Behavior → Behavior; Event → Behavior; Behavior → Event.       | Time-ordered: source causes target to start / occur. Used for control flow.                              |
| **Flow**        | §5.3.2  | Behavior → Behavior.                                            | Information / data / value transferred from source to target. Used for information flow.                |

### Other Relationships (§5.4)

| Relationship       | Spec §  | Source → Target pattern              | Semantics                                                              |
|--------------------|---------|---------------------------------------|------------------------------------------------------------------------|
| **Specialization** | §5.4.1  | Sub-type → super-type.                | The source is a kind of the target. Inheritance of properties / relations. |

### Junctions (§5.5)

A **Junction** is a graphical connector that combines or splits
relationships of the same type. Two kinds:

- **And-junction** — all the connected relationships must hold.
- **Or-junction** — at least one of the connected relationships
  holds.

Junctions are used to model many-to-many connections compactly
and to express logical structure (e.g., a Goal is realized when
*all* of three Requirements are met = And-junction).

### Multiplicity (§5.6)

Each ArchiMate relationship type has a default multiplicity
(0..1, 0..*, 1..1, 1..*). The spec specifies the cardinality for
each relationship type. Annotating multiplicity on a diagram is
permitted and is useful when the default is ambiguous.

### Derivation of Relationships (§5.8)

Some relationships *imply* others. ArchiMate defines derivation
rules so that a model is internally consistent without explicit
representation of every implied relationship. Examples:

- Composition implies Aggregation.
- Realization across a chain (A realizes B, B realizes C) can
  often be derived as A realizes C (subject to spec rules).

The full derivation table is in spec Appendix B; valid
relationships and derivation rules are normative.

## Stakeholders, Views, and Viewpoints

Spec §13.

- **Stakeholder** (§13.2) — same element as in the Motivation
  Domain; here the focus is on how Stakeholders' *concerns*
  drive the choice of architecture views.
- **View** (§2.4) — a representation of a system from the
  perspective of related concerns. Realised by a model fragment
  drawn from the architecture.
- **Viewpoint** (§2.5, §13.3) — a specification of the
  conventions for selecting, classifying, and presenting
  concepts of the model in views. Defines what kind of
  Stakeholder concerns a View addresses.

ArchiMate defines an extensible set of **example viewpoints**
in §13.5 and Appendix C — Capability Map, Business Process View,
Application Cooperation View, Layered View, etc. — each tailored
to specific Stakeholder concerns.

The Viewpoint mechanism (§13.4) lets architects define new
viewpoints for project-specific concerns, classify them, and use
them to produce reusable views.

## Language Customization

Spec §14. ArchiMate 4 allows controlled extension of the
language by:

- **Specialization of element types** — a customised element
  type that is a sub-type of a stock element, inheriting its
  semantics and relationships.
- **Adding attributes** — extra properties on stock or
  customised element types.

Customizations are local to a project and must remain
distinguishable from the standard language. The customization
mechanism is the formal way to add domain-specific concepts
without violating conformance.

## See also

- [`archimate-vocabulary.md`](archimate-vocabulary.md) — how
  this project specifically maps its concepts to the elements
  above. Read after this file.
- [ADR 0014](adr/0014-archimate-across-all-layers.md) — the
  decision that brought ArchiMate 4 into this project.
- ArchiMate® 4 Specification (The Open Group, 2026) — the
  normative source. Section numbers above point into it.
