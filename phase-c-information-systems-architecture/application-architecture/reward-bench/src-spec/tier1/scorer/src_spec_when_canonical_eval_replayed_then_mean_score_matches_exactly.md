# `src_spec_when_canonical_eval_replayed_then_mean_score_matches_exactly`

`run_canonical_eval(solver_factory)` is deterministic with respect to
the input solver class and the canonical seed list. No new code in
`src/tier1/scorer.py` — the determinism flows from:

- `GameBoard(seed=...)` seeds its internal `random.Random`, so tile
  spawns are reproducible per seed.
- The reference solver (and any compliant Tier 1 solver) is itself
  deterministic given its initial state.
- `run_canonical_eval` creates a fresh `solver_factory()` per seed —
  no cross-game state leak.

This cycle pins the Stage 3 replay-determinism contract. If a future
solver introduces wall-clock randomness (e.g., `time.time()`), this
test catches it.
