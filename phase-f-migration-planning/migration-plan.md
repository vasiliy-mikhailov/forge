# Implementation and Migration Plan

The sequenced execution of the Phase E roadmap — TOGAF Phase F's
named deliverable, in forge form.

Each row below is one Phase F experiment. The order is the
landing order — earlier rows must land before later rows because
they unblock them. Each row points at its (planned or active)
experiment spec under [`experiments/`](experiments/).

## Active sequence

| # | Experiment id (planned)         | Closes                                    | Blocks                                                   | Estimated wall    | State          |
|---|---------------------------------|-------------------------------------------|----------------------------------------------------------|-------------------|----------------|
| 1 | `H1-contract-prewrite.md`       | R-D-contract-prewrite                     | re-test of any LLM model swap                            | 1-2 architect-days | spec to be opened |
| 2 | `H2-xref-linter.md`             | R-D-contract-xreflint                     | re-test of any LLM model swap                            | 0.5-1 architect-day | spec to be opened |
| 3 | `J1-daemonize-embed.md`         | R-D-retrieval-cost                        | pilot-wall L2 (~50-90 min/module)                        | 1-2 architect-days | spec to be opened |
| 4 | `J2-kvcache-subagent.md`        | R-D-orchestration-kvcache                 | pilot-wall L2 (compounds with #3)                        | 1-2 architect-days | spec to be opened |
| 5 | `G4-or-G5-model-reswap.md`      | R-B-svcop-thruput (re-test)               | (none — opens only after #1-#3 land)                     | TBD               | gated on 1-3   |

The id-letter convention is informal: `G*` for component-swap
experiments, `H*` for contract-enforcement experiments, `J*` for
runtime-overhead experiments. Numbering inside each letter is
chronological.

## Why this order

- **#1 before #2**: #1 prevents a class of violations from being
  written at all; #2 catches the rest at commit. #1 is the
  cheaper write; #2 needs #1's vocabulary.
- **#1+#2 before #3**: with the contract enforced, #3's wall-time
  improvement is measurable cleanly. Without #1+#2, faster wall
  just produces more violations faster.
- **#3 before #4**: #3 is server-side (`embed_helpers.py`), no
  upstream dependency. #4 needs OpenHands SDK + vLLM cooperation
  and is more invasive.
- **#5 only after #1-#3**: re-running a model swap before contract
  enforcement is set is a third repeat of the G2/G3 falsification.
  Hold the swap until the contract is actually enforced.

## Skipped / not-on-the-trajectory

- **24 h stability run** (R-B-svcop-stable24h) — parked until
  pilot-wall is at L2 (each pilot must be cheap enough to run
  repeatedly).
- **Multi-pilot batching** — vLLM batching would amortise prefill
  across requests, but at single-pilot scale it doesn't apply.
  Re-evaluate when ≥ 2 labs queue inference work concurrently.

## Cross-references

- Roadmap (Phase E):
  [`../phase-e-opportunities-and-solutions/roadmap.md`](../phase-e-opportunities-and-solutions/roadmap.md).
- Requirements catalog:
  [`../phase-requirements-management/catalog.md`](../phase-requirements-management/catalog.md).
- Requirements traceability:
  [`../phase-requirements-management/traceability.md`](../phase-requirements-management/traceability.md).
- Closed predecessors:
  [`experiments/G1-blackwell-stability.md`](experiments/G1-blackwell-stability.md),
  [`experiments/G2-MoE-faster-inference.md`](experiments/G2-MoE-faster-inference.md),
  [`experiments/G3-gemma-4-31b.md`](experiments/G3-gemma-4-31b.md).


## Measurable motivation chain
Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: Phase F's TOGAF-canonical deliverable is the
  Implementation and Migration Plan; this file IS that.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: each row below ties one Phase F experiment
  to its prerequisites + its closure trigger.
- **Measurement source**: experiment-closure: G1 (PASS), G2 (FAIL), G3 (FAIL), K1 (in flight), K2 (in flight) — count of closed/in-flight Phase F rows
- **Contribution**: migration discipline reduces deploy-incident class; contributes to Quality KR.
- **Capability realised**: Architecture knowledge management.
- **Function**: Sequence-Phase-F-experiments.
- **Element**: this file.
