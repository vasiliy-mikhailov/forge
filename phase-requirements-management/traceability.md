# Traceability

Worked example traces showing how a requirement flows from a
Phase A goal through the Core Layers to a Phase F experiment and
back to Phase H promotion (or Phase F replacement on falsification).

These are the load-bearing examples of how Requirements Management
operates in forge.

## Trace 1 — pilot wall reduction (TTS / Architect-velocity)

```
Phase A goal:  Architect-velocity ↑  (every minute the architect
                                      doesn't spend rerunning failed
                                      pilots is a minute of real work)
                            │
                            ▼
Phase B cap:   Service Operation
               quality dim:  throughput
               L1 (today):   ~47 tok/s decode, ~169 min pilot wall
               L2 (next):    ≥ 100 tok/s, ~50-90 min pilot wall
               req id:       R-B-svcop-thruput
                            │
                            ▼
Phase D svc:   LLM inference
               component:    vLLM 0.19.1 + Qwen3.6-27B-FP8 on Blackwell
                            │
                            ▼
Phase F G2:    Hypothesis: swap to MoE Qwen3.6-35B-A3B
               Outcome:    FALSIFIED — decode +4.1× but pilot
                          wall regressed (per-claim overhead is the
                          binding lever, not decode rate).
                            │
                            ▼
Phase F G3:    Hypothesis: swap to dense Gemma-4-31B
               Outcome:    FALSIFIED at gate-4 (cross-ref integrity).
                            │
                            ▼
New sub-reqs:  R-D-retrieval-cost          (Phase D, vector retrieval)
               R-D-orchestration-kvcache   (Phase D, agent orchestration)
               R-D-contract-prewrite       (Phase D, contract enforcement)
               R-D-contract-xreflint       (Phase D, quality grading)
                            │
                            ▼
R-B-svcop-thruput stays OPEN. Re-test model swap once any of the
sub-reqs lands.
```

This trace is currently the most active in forge. It demonstrates
the **falsification-emits-sub-requirements** pattern: a closed-
failed experiment doesn't just close — it splits the original req
into smaller reqs that need to land first.

## Trace 2 — concept-count parity vs Opus (closed)

```
Phase A goal:  TTS  (a wiki with poor concept coverage saves less
                    reader time than one with full coverage)
                            │
                            ▼
Phase B cap:   Concept extraction + linking
               quality dim:  concept count vs Opus baseline
               L1 (was):     44 concepts on module 005, vs Opus 59 (−25%)
               L2 (was):     concept count → Opus parity (+25%)
               req id (was): R-D8-find-concepts
                            │
                            ▼
Phase F D8 task #1 (closed): wire find-concepts into curator with
                              0.85 dedup threshold
               Outcome:      PASS. Pilot v5 measured 48 concepts on
                            module 005, within 20% of Opus, structural
                            compliance clean (3 violations vs Opus 5).
                            │
                            ▼
Phase H promo: L2 → new L1. Phase B capability row updated:
               "concept extraction + linking" L1 now reads "find-concepts
               wired, threshold 0.85, ≥ Opus-class on module 005."
               R-D8-find-concepts row deleted from catalog (git is the
               archive).
```

This trace illustrates a clean closure: experiment passes, Level
2 promotes, the catalog row is deleted, and the Phase B doc reads
as if today's Level 1 has always been the truth.

## Trace 3 — architect edit loop (TTS not directly; Architect-velocity)

```
Phase A goal:  Architect-velocity ↑
                            │
                            ▼
Phase D svc:   (none formally — this is a tooling-tier requirement
                that doesn't realise a forge product capability,
                but does directly move the Phase A goal)
                            │
                            ▼
Side-experiment during G3 work: ssh round-trip cold ~3 s × 50-100
                                edits per session = 15-25 min of
                                handshake overhead per session.
                            │
                            ▼
ADR 0009 (Phase D — but workstation-only, not a forge component):
               ssh ControlMaster → ~0.4 s per edit (4-9× speedup).
                            │
                            ▼
Captured as architect-velocity finding; no Phase B / D trajectory
needed because the lever is workstation-side, not platform-side.
```

This trace illustrates that **not every requirement decomposes
into a Phase B / D quality-dim trajectory**. Some are tooling-
tier (workstation, IDE, ssh config). Those land as ADRs in the
relevant phase folder but don't need a row in
[`catalog.md`](catalog.md) — they don't compete for the same
experiment-budget that Phase F manages.

## Pattern summary

- **Phase A goal** is the *terminal answer* every trace points
  back to.
- **Phase B / D quality-dim trajectory** is the *measurable
  intermediate* — the thing experiments aim at.
- **Phase F experiment** is the *closure attempt* — pass and
  promote, or fail and emit sub-requirements.
- **Phase H** is where promotion is *recorded* — and the prior
  Level 1 description gets *deleted* from the working tree.
- **Requirements Management (this folder)** is the *register*
  that ties the steps together so a reader landing in any phase
  can trace upward to the goal and downward to the closure
  attempt.
