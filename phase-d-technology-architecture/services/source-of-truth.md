# Service: Source-of-truth + per-experiment branch storage

- **Component:** GitHub remotes —
  - `kurpatov-wiki-raw` (transcripts, pushed by raw-pusher).
  - `kurpatov-wiki-wiki` (compiled wiki; experiment branches
    `experiment/D*-...-<served>`; canonical tags
    `canonical/<model>/<module>/<date>`).
  - `tarasov-wiki-raw` / `tarasov-wiki-wiki` — same shape, second
    product.
  - `forge` — the framework repo itself.

## Quality dimensions and trajectories

- **Capacity / quota** — L1: 50 GB-class repos within free quota;
  bench branches for every pilot. L2: stable.
- **Branch hygiene** — L1: `bench/<date>-<served>` for skill v1
  baselines, `experiment/<id>-<date>-<served>` for skill v2
  experiments, `canonical/...` tags for promoted modules.
  Stale experiment branches purged before re-running same id.


## Measurable motivation chain
Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: forge has multiple sources of state (git, vault,
  GitHub repos); needs an explicit source-of-truth declaration
  per data-set.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: each data-set declares its canonical home; ADRs
  cite this file when changing residency.
- **Measurement source**: audit-predicate: P11 (every cross-reference resolves to its declared canonical source)
- **Contribution**: audit-predicate enforcement — each PASS prevents one infrastructure-domain incident class; contributes to Quality KR pre_prod_share.
- **Capability realised**: Architecture knowledge management.
- **Function**: Declare-source-of-truth-per-data-set.
- **Element**: this file.
