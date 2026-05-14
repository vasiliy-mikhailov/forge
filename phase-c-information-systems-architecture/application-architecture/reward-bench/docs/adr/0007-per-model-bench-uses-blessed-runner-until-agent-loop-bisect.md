# ADR 0007 — Per-model bench uses a "blessed runner" until the agent_loop regression is bisected

## Status

Superseded by cycle 67 (2026-05-14). The active `src/tier1/agent_loop.py` reached parity per cycle 67 (canonical mean=15,918 on qwen3.6-27b-awq, beating the legacy reference of 11,734). The blessed-runner workaround is no longer needed. Cycle 68 deleted `src/tier1/legacy_agent_loop.py`, `_bak/`, the per-model bak-runner test, and `docs/hypotheses_agent_loop_regression.md`.

## Context

[ADR 0001](0001-condenser-uses-same-model-as-bench.md) +
[ADR 0005](0005-plateau-detection-supervisor-via-llm-self-judgment.md)
both target the active `src/tier1/agent_loop.py`. Cycles 22-39 reshaped
that loop substantially (cycle 12 prompt drift, cycle 27 per-game
preemption, cycle 31-35 supervisor stack, cycle 38 stall detection,
cycle 39 prompt revert).

In cycle 40 we discovered a real regression. Two reproducible facts:

1. The legacy script (now promoted in cycle 47 to `src/tier1/legacy_agent_loop.py`) ran unmodified
   against the current vLLM endpoint (qwen3.6-27b-awq) produces
   `mean_score=10847 / 11734 / 3406` across three seeds — matching
   the historical 2026-05-05 stage2 result of `10884`.
2. The active `src/tier1/agent_loop.py` on the same model + same vLLM
   peaked at `mean_score=6525` across cycles 36-38.

That's a ~40 percent regression somewhere inside our agent_loop
wiring. Bisecting the diff between the two loops (~775 lines vs
~290 lines) is a separate multi-cycle effort.

Meanwhile, the bench is needed to produce per-model leaderboard
cells. We have two unsatisfactory options:

- **A. Block on the bisect.** No multi-model data until the loop is
  fixed. Bad — leaderboard work blocks indefinitely.
- **B. Score with the regressed loop.** Per-model cells would be
  systematically depressed; comparisons across models would be
  meaningful (same depression for all) but the ABSOLUTE numbers
  wouldn't be reproducible against `_bak`'s historical leaderboard.

A third option:

- **C. Score with the legacy loop pinned as a "blessed runner".**
  Run `src/tier1/legacy_agent_loop.py` as a subprocess from the per-model
  test. Numbers match the historical reference. The legacy loop is
  text-stable (no further commits planned) so reproducibility is
  preserved.

## Decision

Adopt option C. Until the regression in `src/tier1/agent_loop.py` is
bisected, per-model bench data points are produced by invoking the
legacy `src/tier1/legacy_agent_loop.py` as a subprocess. The legacy loop is
**the BLESSED RUNNER** for the purpose of multi-model leaderboard
production.

The test that produces per-model artifacts cites THIS ADR (not the
runner path) so that swapping the runner later — once `src/tier1/`
is at parity — is a one-place change with no test_spec churn.

## Consequences

- Per-model artifacts under `experiments/2026-05-14-*-bak-runner.json`
  carry a `"runner"` field. The shape contract (test_spec) requires
  that field to be present but does NOT pin its specific value.
- When the active loop reaches parity, a new ADR will supersede this
  one and the runner field will start carrying
  `src/tier1/agent_loop.py`. Historical artifacts stay valid since
  the runner field documents the producer.
- The `src/tier1/agent_loop.py` regression is tracked separately and
  remains the primary engineering line for the bench itself.

## Related

- [ADR 0001](0001-condenser-uses-same-model-as-bench.md) — same model
  for bench + condenser.
- [ADR 0005](0005-plateau-detection-supervisor-via-llm-self-judgment.md)
  — supervisor stack (cycles 30-35 target the active loop).
- Cycle 40 leaderboard entry in
  [`experiments/leaderboard_data.md`](../../experiments/leaderboard_data.md)
  — the reproduction that confirmed the regression.
