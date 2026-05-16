# ADR 0015 — Canonical bench `hard_wall_sec = 300` (15s/seed effective)

## Status

Accepted (cycle 104). Implemented in cycle 104 via `run_canonical_battery`
default + test_spec pin.

## Context

[ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) defined
the canonical campaign defaults: `max_iters=500, n_trials=10, T=0.7`.
It did NOT specify `hard_wall_sec`. The `BenchConfig` dataclass
defaults to `hard_wall_sec=0.0` ("disabled, matching the legacy
unbounded behavior" per its docstring).

[ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
established a Docker-sandboxed scoring layer with walltime budget but
applied it specifically to the dev / smoke feedback path. Cycle 78
smoke explicitly set `hard_wall_sec=60` (60 s aggregate, ~12 s/seed
over 5 dev seeds). Canonical mode never inherited this discipline.

Cycle 102's `run_canonical_battery` constructed
`BenchConfig(max_iters=500, n_trials=1, temperature=0.7)` — no
`hard_wall_sec` override → inherits 0.0 → unbounded.

The overnight bench (2026-05-16, qwen3.6-27b-fp8 trial 3) hit
exactly this gap: the model's generated Solver progressed slowly enough
to never trip the 60 s stagnation detector but never finished either.
Trial 3 ran for >2 hours of canonical scoring alone, blocking the
sweep at 3/210 trials.

## Decision

Canonical `hard_wall_sec = 300` seconds aggregate across the 20-seed
canonical game set. With cycle 23/27 per-game timeout deriving from
remaining budget, the worst-case first game gets ~300 s, but the
AVERAGE per-seed share is `300 / 20 = 15 s/game`.

Rationale for 300 s specifically:
  - **Symmetry with cycle 78 smoke:** smoke used 60 s aggregate over
    5 dev seeds = 12 s/seed. Scaling to canonical's 20 seeds at the
    same per-seed rate would give 240 s. Round up to 300 s for slack.
  - **Cycle 77 dev/canonical alignment:** cycle 77 made `dev_hard_wall_sec`
    proportional to canonical via `canonical * 5 / len(seeds)`. With
    canonical=300, dev derives `300 * 5 / 20 = 75 s`. That preserves
    the cycle 77 invariant.
  - **Trial time budget bound:** at 300 s canonical + ~30 s agent loop
    + ~30 s vLLM warmup per trial, worst-case trial = ~6 min. Full
    sweep (210 trials) = ~21 GPU hours worst-case. Acceptable.
  - **Legitimate slow Solvers** (expectimax depth=4, careful tree
    search): 15 s/seed is enough headroom in most observed cases.
    Pathological cases get walltime_exceeded sentinels and the bench
    moves on — that IS the verdict, not a bench bug.

## Consequences

+ Single trial cannot consume the entire sweep budget.
+ Sweep wall-time bound is predictable and presentable.
+ Slow Solvers get a clear `walltime_exceeded` final_state per seed,
  visible in the artifact — the leaderboard distinguishes "actually
  slow" from "bench got stuck".
+ Cycle 77 dev/canonical alignment invariant is preserved.
- A Solver that legitimately plays 20 long games (> 5 min total) gets
  a partial sentinel. We accept this trade-off: at canonical's T=0.7
  and N=10 trials, the model has many chances to produce a faster
  variant. If most trials hit the cap, the model's mean reflects it.
- Pre-cycle-104 artifacts (e.g. the 3 qwen3.6-27b-fp8 trials from
  the overnight run) were written without the cap. They remain valid
  individual measurements but were generated under a different
  budget; the leaderboard footnote will note this for runs predating
  cycle 104.

## Path forward

- **Cycle 104** (this ADR's implementation):
  - `run_canonical_battery` default sets `hard_wall_sec=300` on the
    `BenchConfig` it passes to `main()`.
  - Parameter `canonical_hard_wall_sec=300` exposed; callers can
    override per-sweep if needed.
  - Test_spec pins the wiring.
  - The interrupted trial 3 is re-attempted on next sweep start.

## Related

- [ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) —
  canonical campaign defaults. ADR 0015 fills the unspecified
  `hard_wall_sec` slot.
- [ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
  — walltime budget concept. ADR 0015 extends it from dev/smoke to
  canonical.
- Cycle 77 (dev/canonical per-seed alignment) — invariant that
  preserves the proportionality.
- Cycle 78 smoke v2 — used `hard_wall_sec=60` over 5 dev seeds; ADR
  0015 scales this to canonical.
