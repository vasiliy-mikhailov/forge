# Application components (labs)

Forge has four application components, each a cohesive group of
software functionality. Implementation lives at
`<this-folder>/<component>/`; each component carries its own
AGENTS.md (Phase A-H scoped) plus Dockerfile / docker-compose /
SPEC.

| Component       | Forge capabilities it realises                                                                                       | Serves products   |
|-----------------|----------------------------------------------------------------------------------------------------------------------|-------------------|
| `wiki-compiler` | Service operation (LLM inference); R&D (Blackwell stability — G1)                                                   | All wiki products |
| `wiki-bench`    | R&D (benchmarking + experimentation); Product delivery (canonical wiki); Architecture knowledge mgmt (skill v2)     | All wiki products |
| `wiki-ingest`   | Service operation (transcription pipeline); Product delivery (raw.json publication)                                 | All wiki products |
| `rl-2048`       | R&D (RLVR methodology); Service operation (Jupyter / MLflow)                                                        | rl-2048           |

The `wiki-*` components are content-agnostic — the same
infrastructure serves every wiki product. Adding a new wiki
product (e.g. for a new author/corpus) requires only a new pair of
`<author>-wiki-{raw,wiki}` GitHub repos plus per-pilot env config;
no component change needed.


## Motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: forge needs an Application Components catalog to
  enumerate the Labs as ArchiMate Application Components.
- **Goal**: Architect-velocity (one place to look up which
  Lab is which).
- **Outcome**: 4 Labs (rl-2048, wiki-bench, wiki-compiler,
  wiki-ingest) listed; each cited from the per-product
  Capability files.
- **Capability realised**: Architecture knowledge management.
- **Function**: Catalogue-Application-Components.
- **Element**: this file.
