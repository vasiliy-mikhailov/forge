# Capability: Develop wiki product line

A Phase B capability decomposing forge's
[forge-level R&D + Product delivery + Architecture-knowledge-management
capabilities](forge-level.md) into the wiki-specific activity:
*the ability to take an author's lecture corpus and produce a
smart-reading wiki that preserves the author's voice while
saving the reader 50-90 minutes per lecture, repeatably across
multiple author corpora*. Exercised across every member of the
[Wiki product line](../products/wiki-product-line.md) (Kurpatov,
Tarasov, future authors).

This capability covers wiki development as a *behaviour* (steps
the labs run, properties of the resulting artifacts); the
concrete labs and tech stack that realise it live in
[Phase C application architecture](../../phase-c-information-systems-architecture/application-architecture/)
and [Phase D technology architecture](../../phase-d-technology-architecture/).

## Quality dimensions

Each dimension is a measurable property of a wiki the line
produces. Per-product trajectories may differ (Kurpatov is at one
Level 1 / Level 2 pair, Tarasov at another), but the *dimensions*
are identical — that's what makes this a single capability.

| Dimension                           | Realised in            | Metric / property                                                                                                                                               |
|-------------------------------------|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Requirement traceability**        | (architect)            | Every implementation choice (prompt rule, schema field, grader check) cites an `R-NN` from `phase-requirements-management/catalog.md`. No orphan rules.         |
| **Voice preservation**              | wiki-bench             | Narrative sections (`## TL;DR`, `## Лекция`) retain the author's tone, sceptical asides, characteristic metaphors. Structural sections stay neutral.            |
| **Reading speed**                   | wiki-bench             | Reader gets the gist of a lecture in 1–2 minutes via TL;DR + bullets + cross-links; full read in 5–15 minutes.                                                  |
| **Transcription accuracy**          | wiki-ingest            | Russian-WER on a held-out audit set.                                                                                                                              |
| **Dedup correctness**               | wiki-bench             | Cross-source `REPEATED` markers; retrieval-augmented; no claim appears as `NEW` twice across sources.                                                            |
| **Fact-check coverage**             | wiki-bench             | Empirical claims carry Wikipedia / primary-source URLs; contradicted claims marked `CONTRADICTS_FACTS`. No claim slips through unflagged.                       |
| **Concept-graph quality**           | wiki-bench             | Canonical skill v2 shape; every concept linked from ≥ 1 source; cross-refs between concepts populated.                                                          |
| **Reproducibility**                 | wiki-bench             | A run can be reproduced from `(Dockerfile + raw repo)` only; same model + same raw → byte-identical wiki.                                                       |

The "Voice preservation" and "Requirement traceability" dimensions
are the two active trajectories — see the catalog rows
`R-B-voice-preservation` and `R-B-wiki-req-collection` in
[`../../phase-requirements-management/catalog.md`](../../phase-requirements-management/catalog.md).
The other dimensions are at Level 1 stable today.

## Realised by

The labs that physically exercise the capability:

- **`wiki-ingest`** ([`../../phase-c-information-systems-architecture/application-architecture/wiki-ingest/`](../../phase-c-information-systems-architecture/application-architecture/wiki-ingest/))
  — the **Transcription** sub-activity.
  Faster-whisper, Russian-tuned model, watcher daemon ingests
  audio/video → `raw.json` whisper segments. Realises the
  Transcription accuracy dimension.
- **`wiki-bench`** ([`../../phase-c-information-systems-architecture/application-architecture/wiki-bench/`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/))
  — the **Compilation** sub-activity.
  Agent harness + Python coordinator (per
  [ADR 0013](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/)).
  Realises Voice preservation, Reading speed, Dedup correctness,
  Fact-check coverage, Concept-graph quality, Reproducibility.
- **`wiki-compiler`** ([`../../phase-c-information-systems-architecture/application-architecture/wiki-compiler/`](../../phase-c-information-systems-architecture/application-architecture/wiki-compiler/))
  — the **LLM serving** sub-activity (vLLM at
  `inference.mikhailov.tech`). Realises Reproducibility (in part)
  and is the dependency wiki-bench calls into. Its own
  capability angle is [Service Operation](service-operation.md).
- **(architect)** — the **Wiki requirements collection**
  sub-activity (process at
  [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)).
  Realises Requirement traceability.

The fact that one of the four sub-activities is "(architect)"
rather than a lab is intentional: requirements collection is
human-driven by design (see ADR rationale in
[`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)).

## Decomposition into Phase D sub-trajectories

When a Voice-preservation or Requirement-traceability trajectory
gets blocked at the lab level, sub-trajectories are emitted into
Phase D. Today's open ones (also rows in
[`../../phase-requirements-management/catalog.md`](../../phase-requirements-management/catalog.md)):

- **R-D-contract-prewrite** — concept-existence check inside
  curator loop.
- **R-D-contract-xreflint** — fail-fast cross-ref linting after
  each commit.
- **R-D-retrieval-cost** — daemonize embed_helpers.

These are not unique to this capability (Service Operation also
references them), but they gate Voice-preservation closure.

## Consumed by

The [Wiki product line](../products/wiki-product-line.md), and
through it every product on that line:

- [Kurpatov Wiki](../products/kurpatov-wiki.md)
- [Tarasov Wiki](../products/tarasov-wiki.md)
- Future authors (joining the line via
  `<author>-wiki-{raw,wiki}` repos + per-pilot env config).

Adding a new product to the line consumes this capability without
extending it — that's what makes it a *line*-level capability
rather than a per-product one.

## Reference

- Forge-level capabilities this decomposes:
  [`forge-level.md`](forge-level.md) (R&D + Product delivery +
  Architecture knowledge management).
- Sibling capability used by the same labs:
  [`service-operation.md`](service-operation.md).
- Phase H trajectory rule:
  [`../../phase-preliminary/architecture-method.md`](../../phase-preliminary/architecture-method.md).
- Active experiment specs:
  [`../../phase-f-migration-planning/experiments/`](../../phase-f-migration-planning/experiments/).
