# `src_spec_attempt_result_entity`

`src.tier1.entities.attempt_result.AttemptResult` is a frozen `dataclass`
holding the aggregate outcome of one Tier-1 canonical eval. Pure
domain type — no IO, no HTTP, no external systems.

Fields (aligning with SPEC.md Tier 1 `AttemptResult` schema):

  games                   tuple[GameResult, ...]
  stagnation_sec          float
  hard_wall_sec           float
  stagnated_any           bool
  walltime_exceeded       bool
  mean_score              float
  median_score            float
  std_score               float
  max_max_tile            int
  n_games                 int
  aggregate_walltime_sec  float
  seeds                   tuple[int, ...]

`games` is the new SPEC.md-aligned field carrying per-game
`GameResult` records. It defaults to `()` so existing constructors
continue to work; later cycles will populate it from the adapter
and eventually drop the legacy `seeds` field.

Allowed imports (kept minimal to satisfy the entities-purity rule):

  dataclasses, typing

The dataclass is `frozen=True` so instances are hashable / immutable
value objects — matches Clean Architecture's idea that entities
represent unchanging facts about a finished attempt.


`stagnation_sec` is the per-game progress-watchdog threshold from
SPEC.md §"Per-game stagnation detector" (default 60 s). The
attempt record carries the value that applied to the run so later
analysis can distinguish attempts with different settings.

`hard_wall_sec` is the outer runaway-protection cap from
SPEC.md §"Per-game stagnation detector" (default `0` = disabled).
The attempt record carries the cap that applied so later analysis
can distinguish attempts run with vs without the safety net.

`stagnated_any` is the observation flag mirroring SPEC.md: `True`
if any game in `games` ended with `final_state='stagnated'`. Carries
no logic itself; the populating use case (`score_submission`) is
responsible for setting it correctly. Default `False`.

`walltime_exceeded` is the observation flag mirroring SPEC.md:
`True` if any game in `games` ended with
`final_state='walltime_exceeded'` (the outer `hard_wall_sec` cap
fired). Default `False`.
