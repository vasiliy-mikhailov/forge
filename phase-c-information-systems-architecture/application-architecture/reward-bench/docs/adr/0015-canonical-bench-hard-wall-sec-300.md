# ADR 0015 — Canonical bench `hard_wall_sec = 300` (15s/seed effective)

## Status

Accepted (cycle 104). Implemented in cycle 104 via `run_canonical_battery`
default + test_spec pin.

## Context

[ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md)
defined canonical defaults but not `hard_wall_sec`; `BenchConfig`
defaults to `0.0` (unbounded).

[ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
applied the walltime budget to dev/smoke only. Smoke uses
`hard_wall_sec=60` (12 s/seed over 5 seeds). Canonical never
inherited the discipline.

`run_canonical_battery` constructs `BenchConfig(max_iters=500,
n_trials=1, T=0.7)` — no `hard_wall_sec` override → unbounded.

The 2026-05-16 overnight bench (qwen3.6-27b-fp8 trial 3) hit this:
the Solver progressed slowly enough to never trip the 60 s stagnation
detector but never finished. Trial 3 ran >2 hours of canonical
scoring, blocking the sweep at 3/210.

## Decision

Canonical `hard_wall_sec = 300` aggregate across 20 seeds. Average
per-seed share: `300 / 20 = 15 s/game`.

Rationale for 300 s:

- **Symmetry with smoke**: smoke 60 s / 5 seeds = 12 s/seed; scaled to
  20 seeds = 240 s; rounded up to 300 s for slack.
- **dev/canonical alignment**: `dev_hard_wall_sec = canonical * 5 /
  len(seeds)` → with canonical=300, dev = 75 s. Preserves invariant.
- **Sweep budget bound**: ~6 min/trial worst case × 210 trials ≈ 21
  GPU-hours. Acceptable.
- **Legitimate slow Solvers**: 15 s/seed covers most expectimax depth-4
  cases; pathological ones get `walltime_exceeded` sentinels — that
  IS the verdict.

## Consequences

+ One trial can't consume the sweep budget.
+ Sweep wall-time is predictable.
+ Slow Solvers get `walltime_exceeded` per seed — leaderboard
  distinguishes slow from stuck.
+ dev/canonical alignment preserved.
- A Solver that legitimately needs > 5 min total gets a partial
  sentinel. Acceptable: T=0.7, N=10 trials give many shots.
- Pre-cycle-104 artifacts were written unbounded; leaderboard footnote
  notes the budget change.

## Path forward

- `run_canonical_battery` default `hard_wall_sec=300`.
- Param `canonical_hard_wall_sec=300` exposed for per-sweep override.
- Test_spec pins the wiring.
- Interrupted trial re-attempted on next sweep.

## Related

- [ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) —
  fills the unspecified `hard_wall_sec` slot.
- [ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
  — extends the walltime budget from dev/smoke to canonical.
