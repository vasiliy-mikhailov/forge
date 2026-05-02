# Data sets

| Data set                       | Shape                                                                                            |
|--------------------------------|--------------------------------------------------------------------------------------------------|
| `kurpatov-wiki-raw`            | per-source `raw.json` (whisper segments)                                                         |
| `tarasov-wiki-raw`             | per-source `raw.json` (whisper segments) — same shape, second product                            |
| `kurpatov-wiki-wiki:skill-v2`  | `data/sources/<slug>.md`, `data/concepts/<slug>.md`, `data/concept-index.json`                   |
| `tarasov-wiki-wiki:skill-v2`   | same shape; pre-pilot                                                                            |
| Bench artefacts                | `${STORAGE_ROOT}/labs/wiki-bench/experiments/<run_id>/`                                          |
| Retrieval index (D8)           | `wiki/data/embeddings/{claims,concepts}.{sqlite,npz}` (numpy + sqlite hybrid)                    |

Per-product detailed shapes live in their lab's
`STATE-OF-THE-LAB.md`.


## Measurable motivation chain (OKRs)
Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: forge needs a Data Sets catalog (raw.json,
  source.md, concept.md, etc.) at the Phase C data-
  architecture layer.
- **Goal**: Architect-velocity (data-set names cited
  consistently across Labs + Roles).
- **Outcome**: every Phase B Role's "Inputs / Outputs"
  section names data-sets that exist here.
- **Measurement source**: n/a — declarative: data-set catalog; integrity check is P11 (cross-references resolve)
- **Capability realised**: Architecture knowledge management.
- **Function**: Catalogue-Data-Sets.
- **Element**: this file.
