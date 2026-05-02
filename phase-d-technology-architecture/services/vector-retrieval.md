# Service: Vector retrieval (claim and concept dedup)

- **Component:** `orchestrator/embed_helpers.py` +
  `intfloat/multilingual-e5-base` + numpy + sqlite. Index lives in
  the wiki repo at `wiki/data/embeddings/{claims,concepts}.{sqlite,npz}`.
- **Lab:** [`wiki-bench/`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/).

## Quality dimensions and trajectories

- **Claim retrieval** — L1: wired into source-author per-claim via
  `find-claims --k 5`; threshold 0.78 for REPEATED (calibrated
  against e5-base paraphrase distribution — see step9 synth gate).
- **Concept retrieval** — L1: wired into curator (D8 task #1
  closed). Threshold 0.85 near-lexical, 0.78-0.85 paraphrase,
  < 0.78 keep proposed. Module 005 pilot v5 result confirmed.
- **Per-call cost** — L1: per-CLI fork of `embed_helpers.py`
  re-loads e5-base (~280 MB) — ~5 s per invocation. At 100 claims ×
  200 sources scale this is ~28 hours of pure model-load.
  L2: embed_helpers daemonized so the model loads once per pilot,
  not once per claim. (Active trajectory — surfaced as the binding
  lever in G2 close-out: per-claim overhead, not decode rate, is
  what bounds pilot wall.)

## Cross-references

- [`../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0010-retrieval-augmented-dedup.md`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0010-retrieval-augmented-dedup.md)


## Measurable motivation chain
Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: source-author + concept-curator need vector
  retrieval to detect REPEATED claims + concept-graph proximity.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: e5-base embedding + per-pilot retrieval index
  (R-D-retrieval-cost trajectory).
- **Measurement source**: catalog-row: R-D-retrieval-cost (e5-base reload cost trajectory)
- **Contribution**: audit-predicate enforcement — each PASS prevents one infrastructure-domain incident class; contributes to Quality KR pre_prod_share.
- **Capability realised**: Service operation + R&D.
- **Function**: Retrieve-by-vector-similarity.
- **Element**: this file.
