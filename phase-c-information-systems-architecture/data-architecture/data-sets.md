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
