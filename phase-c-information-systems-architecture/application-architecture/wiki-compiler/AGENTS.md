# wiki-compiler — agent context

This file follows the same Phase A-H structure as forge-level
`AGENTS.md` (canonical template:
`forge/phase-g-implementation-governance/lab-AGENTS-template.md`). Read forge-level first for cross-cutting rules; this
file is scoped to the compiler lab.

## Phase A — Architecture Vision

**Lab role within forge.** This lab is one of forge's four application components. It realises the following forge-level capabilities for the *LLM inference* domain: **Service operation** (serving the open-weight LLM that other labs consume) and **R&D** (Blackwell stability and inference performance — see experiment G1). It does not own *Product delivery* or *Architecture knowledge management* directly; those are realised through bench.

**Vision (lab-scoped).** Provide the LLM inference service that
realises every wiki-product capability and every future RL trainer's
verifiable reward call. Without compiler, no wiki, no bench, no
program-synthesis loop.

**Lab-scoped stakeholders.**

- **Architect of record** (forge-wide; see `forge/AGENTS.md`).
- **Consumer labs** — `wiki-bench` today, future RL trainers
  tomorrow. The compiler lab's API contract is the
  OpenAI-compatible HTTP endpoint at `${INFERENCE_BASE_URL}`.

**Lab-scoped drivers.**

- GPU instability under sustained 27B-FP8 inference (G1 experiment;
  every crash costs ~30-60 min recovery and aborts whatever pilot is
  in flight).
- GPU $/output token under a single Blackwell card.

**Lab-scoped goals.**

- **Stability** — ≥ 95 % pilot completion rate without GPU recovery.
  Feeds forge-wide architect-velocity.
- **Throughput at memory-bandwidth ceiling** for batch=1 on Qwen3.6-27B-FP8
  (currently ~47 tok/s decode, ~80 % of theoretical ceiling).

**Lab-scoped principles.**

- Single-card vLLM only; the Blackwell hosts compiler OR rl-2048,
  not both.
- Power cap mandatory before vLLM starts
  (`/etc/systemd/system/nvidia-power-limit.service`).
- Pin vLLM image tag; no `:latest`.

## Phase B — Business Architecture

This lab does not own a wiki product capability directly. It owns the
**production-framework** capability that realises every wiki
capability:

| Capability                 | Quality dimension                                    |
|----------------------------|------------------------------------------------------|
| Serve a 27B-class FP8 LLM at 128 K context | Throughput (tok/s decode + prefill); stability (mean-time-to-crash); cost-per-output-token |

Specifically: enable other labs (bench, future RL trainers) to point
an OpenAI-compatible client at `${INFERENCE_BASE_URL}` and get
useful output without reasoning about the underlying serving stack.

## Phase C — Information Systems Architecture

The compiler lab is mostly stateless from a data perspective:

- **Input:** prompt JSON over OpenAI-compatible HTTP API.
- **Output:** completion / chat-completion JSON (also OpenAI shape).
- **On disk:** model weights pulled from HF Hub, cached in
  `${STORAGE_ROOT}/labs/wiki-compiler/hf-cache/`. No
  per-experiment state.

## Phase D — Technology Architecture

**Service: LLM inference** (forge-wide, consumed by bench + future
trainers).

- Component: vLLM 0.19.1 (cu130-ubuntu2404 image) serving
  Qwen3.6-27B-FP8 with YaRN factor 4.0 → 128 K context, single-card
  on the Blackwell.
- Component: caddy 2 (reverse proxy + TLS termination at
  `inference.mikhailov.tech`).
- Component: docker-compose (orchestrates vllm + caddy together).

L1 throughput: ~47 tok/s decode batch=1; ~6.3 K tok/s honest prefill;
prefix cache helps repeated system prompts ~30 %.

L1 stability: 50 % UVM-crash rate within 2.5 h sustained inference at
default vLLM settings. Failure mode is `gdn_linear_attn._forward_core`
→ `cudaErrorLaunchFailure` followed by kernel-side
`BUG uvm_gpu_chunk_5`. Recovery requires `modprobe -r/+ nvidia` or
reboot. Cross-reference: [`forge/phase-f-migration-planning/experiments/G1-blackwell-stability.md`](../../../phase-f-migration-planning/experiments/G1-blackwell-stability.md) (closed 2026-04-27).

L2 stability target: ≤ 5 % crash rate over 7-source pilots —
closed by G1 (400 W power cap + persistence, gpu-memory-utilization
0.85). The next stability target (24 h continuous over 200-source
runs) is currently parked.

**ADRs (Phase D scope).**
- [`docs/adr/0001-vllm-public-openai-compatible-endpoint.md`](docs/adr/0001-vllm-public-openai-compatible-endpoint.md) — vLLM as the public OpenAI-compatible endpoint.
- [`docs/adr/0002-per-model-parsers.md`](docs/adr/0002-per-model-parsers.md) — per-model tool-call / reasoning parsers.

## Phase E — Opportunities and Solutions

Gap analysis for this lab — what capabilities are not yet at Level 2.
If a `STATE-OF-THE-LAB.md` exists, it is the canonical gap audit;
otherwise the Phase H trajectories table below stands in.

## Phase F — Migration Planning

Active experiment specs at `docs/experiments/<id>.md` are the
sequenced work packages closing those gaps. Only Active and
Closed-but-still-cited experiments are kept; superseded ones go to
git history per Phase H.


- **G1 (closed 2026-04-27):** Blackwell stability fix —
  400 W power cap + persistence-mode + gpu-memory-utilization 0.85.
  Service Operation stability dim L1 set at ≥ 169 min sustained.
  Spec at
  [`forge/phase-f-migration-planning/experiments/G1-blackwell-stability.md`](../../../phase-f-migration-planning/experiments/G1-blackwell-stability.md).

## Phase G — Implementation Governance

- **Single-card vLLM only** on the Blackwell. Going to dual-GPU TP
  would take both cards, conflicting with the ingest lab on RTX 5090
  and (when active) rl-2048 — see forge-level "What NOT to do".
- **Power cap is mandatory.** `nvidia-power-limit.service` (400 W
  with `-pm 1`) must be active before vLLM starts. If the unit fails
  to fire, restart it before bringing vLLM up.
- **Don't edit vLLM compose from other labs.** Bench, ingest etc.
  are clients. If the model needs to change: edit `forge/.env`
  (`INFERENCE_MODEL` / `INFERENCE_SERVED_NAME`) and
  `make kurpatov-wiki-compiler-down && make wiki-compiler`.
- **Pin vLLM image tag.** Don't use `:latest`. Bumping is a
  deliberate edit, recorded in git history (and likely an ADR).
- **Hot-swap model swap procedure**: the model registry contract
  is forge-level —
  [`forge/phase-d-technology-architecture/adr/0008-model-registry-single-source-of-truth.md`](../../../phase-d-technology-architecture/adr/0008-model-registry-single-source-of-truth.md).
  Swap by editing `forge/.env: INFERENCE_ACTIVE_MODEL_ID`, then
  `make wiki-compiler-down && make wiki-compiler`.
- **GPU recovery from UVM crash:**
  ```
  sudo modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia
  sudo modprobe nvidia nvidia_uvm
  sudo systemctl restart nvidia-power-limit.service
  docker start vllm-inference
  ```
  After recovery, check that the systemd unit re-applied `400 W`
  with `-pm 1`. If the unit didn't re-fire, run it manually before
  starting vLLM.
- **CUDA-active container clean shutdown:** prefer
  `docker stop --time 10 <name>` over `docker rm -f <name>` to avoid
  leaving orphan kernel-side CUDA contexts (G1-H3).

## Phase H — Architecture Change Management

| Capability | Level 1 (today) | Level 2 (next) | Metric delta |
|------------|-----------------|----------------|--------------|
| Serve 27B-class FP8 LLM at 128 K context | works at default settings, ~50 % crash rate within 2.5 h | ≤ 5 % crash rate, same throughput | Architect-velocity: from ~50 % pilot retry rate to ≤ 5 % |

## Cross-references

- Forge-level: `forge/AGENTS.md` Phase D (service tenancy table) +
  Phase G (per-lab AGENTS.md template, GPU recovery convention).
- G1 experiment (closed):
  [`forge/phase-f-migration-planning/experiments/G1-blackwell-stability.md`](../../../phase-f-migration-planning/experiments/G1-blackwell-stability.md).
- Power-limit unit: `/etc/systemd/system/nvidia-power-limit.service`.


## Motivation chain

Per [P7](../../../../phase-preliminary/architecture-principles.md):

- **Driver**: this Lab realises forge-level Capabilities for the
  *LLM inference* domain; without an AGENTS.md driving the agent
  context, a Cowork session loaded against this lab has no
  Phase A-H scaffolding to anchor on.
- **Goal**: Architect-velocity (one entry-point file per Lab) +
  audit reliability (P9 walks lab AGENTS.md headers for the 8
  Phase A-H sections).
- **Outcome**: every architect / agent session loaded for this
  Lab finds the Phase context here; lab-local docs (SPEC.md,
  smoke.md, backlog, STATE-OF-THE-LAB) are transitively covered
  by this file's chain.
- **Measurement source**: lab-tests: WC (8 phase-section headers + lab-AGENTS-runner band)
- **Capability realised**: Service operation + R&D
  ([forge-level.md](../../../../phase-b-business-architecture/capabilities/forge-level.md)).
- **Function**: Anchor-wiki-compiler-lab-context.
- **Element**: this AGENTS.md.
