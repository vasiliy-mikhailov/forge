# Phase F — Migration Planning

The sequenced work that closes Phase E gaps. Each capability's
trajectory toward Level 2 (TOGAF would call this the Transition
Architecture) lives in one experiment doc per swing.

## Active and recent experiments

- [`experiments/G1-blackwell-stability.md`](experiments/G1-blackwell-stability.md)
  — closed. Service Operation / stability dimension Level 1
  established (400 W cap + persistence-mode is the binding fix for
  UVM crashes).
- [`experiments/G2-MoE-faster-inference.md`](experiments/G2-MoE-faster-inference.md)
  — closed (falsified). Tested Qwen3.6-35B-A3B MoE swap; gate-1
  PASSED (4.1× decode), gate-2 FAILED (pilot quality regression).
  Reverted to Qwen3.6-27B-FP8. Identified per-claim overhead, not
  decode rate, as the binding lever.
- `experiments/G3-gemma-4-31b.md` — in flight (this session).
  Gate-1: Gemma-4-31B-FP8 dense decode 42.3 tok/s vs Qwen-27B's
  47 tok/s, prefill ~30 K with cache-hit. Speed is not the only
  metric — quality pilot underway (N=2 sources).

## ADRs

- [`adr/`](adr/) — Phase F scoped ADRs (migration-time decisions
  that are not specific to a single experiment).

## Convention

- Each experiment is named `<id>-<slug>.md`.
- An experiment doc carries: hypothesis (IF–THEN–BECAUSE),
  falsification criteria, sequenced work, expected outcomes,
  closure notes (PASS / FAIL with measurements).
- Only Active and Closed-but-still-cited experiments stay in this
  folder; superseded experiments go to git history per
  [`../phase-h-architecture-change-management/trajectory-model.md`](../phase-h-architecture-change-management/trajectory-model.md).
