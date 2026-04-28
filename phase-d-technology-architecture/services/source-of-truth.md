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
