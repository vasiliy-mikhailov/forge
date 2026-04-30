# forge — Business Architecture (TOGAF Phase B)

What lives here: the *organizational* shape of forge — roles people
play, business capabilities those roles exercise, and processes that
operationalize those capabilities. Sits at the top level alongside
`labs/`, `products/`, `scripts/`, `tests/`, `docs/` — not under
`docs/`, because these are first-class operational primitives, not
documentation about something else. An ADR is documentation; a
process is a thing the organization does.

## Why this section exists

Recent regressions on `kurpatov-wiki` traced back to *missing
requirements* — implementation choices (prompts, schemas, graders)
made without a stated requirement they were meant to satisfy. The
fix is not a better prompt; it is a discipline that writes the
requirement first, with provenance, and only then writes the
implementation. That discipline needs a named role that owns it
(`roles/wiki-product-manager.md`), a capability that role exercises
(`capabilities/wiki-requirements-collection.md`), and a process
that operationalizes the capability
(`processes/collect-wiki-requirements.md`).

The artifacts in this section are *generic across wiki products*.
Concrete artifacts produced by walking the process for a specific
wiki live under `products/<wiki>/`.

## Layout

```
business/
├── README.md
├── roles/
│   └── wiki-product-manager.md            role definition (TOGAF org map)
├── capabilities/
│   └── wiki-requirements-collection.md    capability statement
└── processes/
    └── collect-wiki-requirements.md       process definition
```

## Relationship to other top-level folders

- `labs/<lab>/` — implementations. A lab consumes the requirements
  catalogue from a `products/<wiki>/` and references R-IDs / QA-IDs
  in its prompts and verifiers.
- `products/<wiki>/` — concrete TOGAF Phase A & C artifacts for one
  wiki product (stakeholders, goals, use-cases, info-arch,
  requirements catalogue, quality attributes, traceability matrix).
  Produced by walking the process in this section.
- `docs/` — narrative architecture and operations docs (cross-lab
  topology, GPU layout, runbooks). Not the place for organizational
  primitives.
- `docs/adr/` — decision records. An ADR is the *outcome* of an
  argument; this section is the *forum* in which the argument
  happens.
