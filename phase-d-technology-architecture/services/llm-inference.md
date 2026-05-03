# Service: LLM inference

- **Component:** vLLM 0.19.1 (cu130) serving Qwen 3.6-27B on the
  Blackwell, 256 K native context, single-card. Active-quantization
  default: NVFP4 (4-bit weights via Blackwell tensor cores; per
  [G4 closure 2026-05-03](../../phase-f-migration-planning/experiments/G4-nvfp4-faster-inference.md)
  — +23 % decode TPS / +42 % prefill TPS vs FP8). FP8 baseline kept in
  the model registry for revert.
- **Realised by:** the `vllm-inference` container, in EITHER of two
  operating units (mutex):
  - the [`wiki-compiler/`](../../phase-c-information-systems-architecture/application-architecture/wiki-compiler/)
    lab (vLLM as part of the wiki-compile pipeline), OR
  - the [`inference/`](../../phase-c-information-systems-architecture/operating-modes/inference/)
    mode (standalone vLLM, no wiki-compile pipeline — per
    [ADR 0028](../../phase-preliminary/adr/0028-inference-mode.md)).
  Both pin `${INFERENCE_GPU_UUID}` on the Blackwell, expose
  `${INFERENCE_DOMAIN}`, and load the active model from the same
  registry via `bin/load-active-model.sh` (per ADR 0008).

## Quality dimensions and trajectories

- **Throughput** — L1: ~47 tok/s decode batch=1, ~6.3 K tok/s
  prefill (raw, honest). L2 target: ≥ 100 tok/s decode (next
  experiment per Phase F backlog; G2 MoE swap was falsified —
  decode is not the binding lever for pilot wall).
- **Stability** — L1: ≤ 5 % UVM-crash rate over 7-source pilots
  (closed by G1: 400 W power cap + persistence-mode +
  `--gpu-memory-utilization 0.85`). L2: stable across 200-source
  runs (≥ 24 h continuous).
- **Latency** (per-LLM-call) — ~5-30 s wall depending on output
  length. Not on the active trajectory.
- **Cost-per-output-token** — ~142 Wh / 1 K output tok (400 W ÷
  47 tok/s × 60). Function of throughput; advances when L1
  throughput moves.

## Cross-references

- [`adr/0005-inference-subsystem.md`](../adr/0005-inference-subsystem.md)
- [`adr/0008-model-registry-single-source-of-truth.md`](../adr/0008-model-registry-single-source-of-truth.md)
- Closed experiment `phase-f-migration-planning/experiments/G1-blackwell-stability.md` (stability dim L1).
- Closed experiment `phase-f-migration-planning/experiments/G2-MoE-faster-inference.md` (throughput dim — falsified).


## Measurable motivation chain
Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: every wiki-compile pipeline needs a long-running
  LLM inference endpoint.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: vLLM serves Qwen 3.6-27B (NVFP4 default per G4
  closure 2026-05-03; FP8 fallback in registry) on the Blackwell
  GPU; OpenAI-compatible; 256 K context.
- **Measurement source**: lab-tests: WC (wiki-compiler smoke + AGENTS Phase A-H integrity)
- **Contribution**: audit-predicate enforcement — each PASS prevents one infrastructure-domain incident class; contributes to Quality KR pre_prod_share.
- **Capability realised**: Service operation
  ([../../phase-b-business-architecture/capabilities/service-operation.md](../../phase-b-business-architecture/capabilities/service-operation.md)).
- **Function**: Serve-LLM-inference.
- **Element**: this file.
