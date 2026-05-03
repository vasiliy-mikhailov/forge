# inference mode — SPEC

This mode provides vLLM-served LLM inference via OpenAI-compatible HTTP API at `${INFERENCE_DOMAIN}`. It is the first **non-lab operating mode** in forge — see [`../README.md`](../README.md) for the mode-vs-lab distinction.

## What this mode IS

- A minimal self-contained implementation: caddy + `vllm-inference` container.
- Same vLLM image, same `${STORAGE_ROOT}/shared/models` HuggingFace cache, same `${INFERENCE_GPU_UUID}` pinning, same `${INFERENCE_DOMAIN}` as the wiki-compiler lab uses for its OWN vllm-inference container.
- Mutex with `wiki-compiler` mode and `rl-2048` mode (Blackwell GPU + caddy ports 80/443).

## What this mode IS NOT

- Not a lab. No `application-architecture/inference/` directory; no AGENTS.md (not an agent operating-environment); no SPEC-extra; no wiki-compile pipeline scripts.
- Not dependent on `wiki-compiler` lab in any way. wiki-compiler stays as-is per architect call. Both modes happen to use the same underlying vLLM image but don't reference each other.
- Not multi-GPU. Same single-Blackwell architecture as wiki-compiler's inference. Combined-two-cards inference rejected for current model size — see [wiki-compiler/SPEC.md § Alternatives rejected](../../application-architecture/wiki-compiler/SPEC.md).

## When to use

- Customer-interview cycle agents need vLLM endpoint without the rest of the wiki-compile pipeline.
- Ad-hoc benchmarking, evaluation runs, or external-consumer usage that doesn't require wiki-compile context.
- Wiki PM or other roles want to invoke vLLM directly via OpenAI SDK against `${INFERENCE_DOMAIN}`.

## How to enter the mode

```
make inference     # or: cd phase-c-…/operating-modes/inference && make up
```

Mutex is operator-managed (`make stop-all` first if another mode holds Blackwell or caddy ports).

## Cross-references

- [`../README.md`](../README.md) — operating modes index.
- [`../../phase-d-technology-architecture/architecture.md`](../../../phase-d-technology-architecture/architecture.md) — physical mapping.
- [ADR 0005](../../../phase-preliminary/adr/0005-inference-subsystem.md) — original inference decision; mode mutex.
- [ADR 0028](../../../phase-preliminary/adr/0028-inference-mode.md) — separate inference mode introduction.
- [ADR 0008 — model registry single-source-of-truth](../../../phase-d-technology-architecture/adr/0008-model-registry-single-source-of-truth.md) — model loading via `bin/load-active-model.sh` (shared with wiki-compiler).

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: customer-interview cycle agents (per ADR 0027) need vLLM without wiki-compile pipeline overhead.
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). One target per operator-intent reduces mode-naming confusion.
- **Outcome**: minimal `make inference` mode landing in this commit; sibling to wiki-compiler / rl-2048 / wiki-ingest / wiki-bench.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: closes the operator-intent-vs-lab-name confusion surfaced in 2026-05-02 architect call.
- **Capability realised**: [Service operation](../../../phase-b-business-architecture/capabilities/service-operation.md).
- **Function**: Provide-vLLM-inference-without-wiki-compile-pipeline.
- **Element**: this mode directory.
