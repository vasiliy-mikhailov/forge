# `src_spec_attempt_result_entity`

`src.entities.attempt_result.AttemptResult` is a frozen `dataclass`
holding the aggregate outcome of one Tier-1 canonical eval. Pure
domain type — no IO, no HTTP, no external systems.

Fields (matching SPEC.md Tier 1 `AttemptResult` schema):

  mean_score              float
  median_score            float
  std_score               float
  max_max_tile            int
  n_games                 int
  aggregate_walltime_sec  float
  seeds                   tuple[int, ...]

Allowed imports (kept minimal to satisfy the entities-purity rule):

  dataclasses, typing

The dataclass is `frozen=True` so instances are hashable / immutable
value objects — matches Clean Architecture's idea that entities
represent unchanging facts about a finished attempt.
