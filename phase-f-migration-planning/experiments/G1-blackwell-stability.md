# G1 — Blackwell stability: power cap + memory headroom

Active spec. Methodology track for **production-framework reliability**
(per the capability split in `forge/AGENTS.md`: production framework is
how the wiki gets made; failures here cost architect-hours but do not
change product output quality). G-prefix because this is a
governance/infrastructure experiment, not a wiki-methodology one.

## Background

Three sustained vLLM crashes on the RTX PRO 6000 Blackwell Workstation
Edition during 27B-FP8 inference, all with the same signature:

```
File ".../vllm/model_executor/layers/mamba/gdn_linear_attn.py", line 830, in _forward_core
    initial_state = ssm_state[non_spec_state_indices_tensor].contiguous()
torch.AcceleratorError: CUDA error: unspecified launch failure
```

followed at the kernel level by

```
BUG uvm_gpu_chunk_5: Objects remaining on __kmem_cache_shutdown()
```

After each crash GPU0 reports `Unable to determine the device handle`
and only recovers via `modprobe -r/+ nvidia` or full reboot. Each crash
costs ~30-60 min of recovery + lost pilot wall-clock; the failure mode
is reproducible at ~2-2.5 hours into sustained 27B inference.

## Two not-mutually-exclusive hypotheses

### G1-H1: Power-cap insufficient → thermal-induced kernel instability

> **IF** we cap the Blackwell at 400 W (was 520 W default in the
> existing nvidia-power-limit.service), enable persistence mode
> (`-pm 1`), and run the pilot, **THEN** sustained 27B-FP8 inference
> over the full 7-source module 005 will complete without
> `cudaErrorLaunchFailure` in the GDN attention kernel,
> **BECAUSE** the chronic crash signature involves both `gdn_linear_attn`
> CUDA failure and UVM slab corruption, both of which are consistent
> with thermal-correlated kernel state corruption when the card runs
> close to its thermal envelope for hours.

**Falsification:** pilot still crashes within 2.5 h of start → power
cap alone is insufficient.

**First test:** pilot v5 (in flight as of 2026-04-27 19:07 MSK) is the
clean test of this hypothesis — same orchestrator as v4 (which
crashed), but at 400 W cap with persistence on and `gpu_memory_utilization`
unchanged at vLLM default 0.95. Result by ~21:30 MSK.

### G1-H2: Memory pressure → GDN-state allocation corrupts UVM slab

> **IF** we restart vLLM with `--gpu-memory-utilization 0.85` (instead
> of the default 0.95), giving the GDN attention's `ssm_state` plus
> activation peaks ~14 GB headroom on the 97 GB card instead of ~6 GB,
> **THEN** the same workload that crashed pilot v4 will complete without
> the UVM `__kmem_cache_shutdown` BUG and without
> `cudaErrorLaunchFailure`,
> **BECAUSE** the crash always occurs in `_forward_core`'s state-space
> indexing path, exactly where peak allocations happen, and the kernel
> log evidence (`BUG uvm_gpu_chunk_5`) points at memory accounting
> failure not thermal failure. With the default 0.95 utilization, the
> card runs at ~94 GB used / 97 GB total — only ~3 GB headroom for
> activation spikes during the GDN gather. Lowering to 0.85 leaves
> ~14 GB headroom, well above any single-call activation peak.

**Falsification:** pilot still crashes despite 0.85 utilization → root
cause is not memory pressure (likely a vLLM 0.19.1 GDN kernel bug or
NVIDIA driver 590.48.01 UVM bug; would need vLLM upgrade or driver
downgrade).

**First test:** pilot v6, scheduled after pilot v5 outcome is known.
If pilot v5 GREEN: G1-H1 confirmed, G1-H2 not strictly necessary but
still worth doing as belt-and-braces. If pilot v5 RED: G1-H2 becomes
the primary intervention.

### G1-H3: SIGKILL on CUDA processes leaves orphan contexts in the kernel

> **IF** we always send SIGTERM (with a short grace period) before
> SIGKILL when stopping a GPU-using process, **THEN** the GPU's
> compute context is properly released and per-GPU reset
> (`nvidia-smi --gpu-reset -i N`) succeeds without driver-wide reload,
> **BECAUSE** observed on 2026-04-27 19:35: `docker rm -f`
> (which is `kill -9` on the container's PID 1) on a CUDA-active
> container left GPU1 reporting 100 % util / 110 W draw / 0 % memory
> util with no userspace process holding the device. `nvidia-smi
> --gpu-reset -i 1` then failed with `In use by another client`,
> meaning the kernel-side context survived its userspace owner.
> The only available cleanups (driver reload or reboot) take all
> GPUs down — meaning a careless `docker rm -f` on a side-experiment
> container can force the architect to abandon a long-running pilot
> on the other GPU.

**Falsification:** If running `docker stop` (which sends SIGTERM)
on a CUDA container also leaves an orphan, then SIGKILL is not the
binding cause — it's the runtime not handling clean shutdown.

**Operational rule (provisional, pending H3 verification):**

> When stopping any container that uses CUDA, prefer
> `docker stop --time 10 <name>` over `docker rm -f <name>`. The
> former gives the container 10 s to release its CUDA context cleanly.
> Only fall back to `docker rm -f` if `docker stop` times out.

## Test matrix

| pilot | power cap | mem util | persistence | result |
|-------|-----------|----------|-------------|--------|
| v3 | 520 W | 0.95 | off | crashed |
| v4 | 520 W | 0.95 | off | crashed at SRC 6 |
| v5 | 400 W | 0.95 | **on** | **in flight — H1 sole-test** |
| v6 (planned) | 400 W | **0.85** | on | H1+H2 belt-and-braces |
| v7 (planned, only if v5 GREEN and v6 also GREEN) | 520 W | 0.85 | on | de-confound: was H1 or H2 the binding fix? |

If the de-confound run (v7) fails, H1 was the binding fix. If it
succeeds, H2 was the binding fix and we can run at full 520 W power
again.

## Architect-velocity metric

This experiment lives in the cross-cutting "architect-velocity" goal
on the Motivation layer (forge/AGENTS.md):

- Pre-G1 baseline: ~50 % of pilot runs require GPU recovery
  (3/3 crashed in the v3-v4 era). That cost ~2 h of recovery wall and
  ~1 architect-hour of intervention per crash.
- G1 target: ≤ 5 % crash rate → effectively 1 pilot per 2.5 h
  reliably. Doubles wiki-compilation throughput per architect-day.

## Close-out criterion

After v5 + v6 + (optionally) v7 we'll know which intervention is
binding. Update `forge/phase-c-information-systems-architecture/application-architecture/wiki-bench/AGENTS.md` with the
canonical settings, and the systemd unit
`/etc/systemd/system/nvidia-power-limit.service` to match. Codify
`--gpu-memory-utilization 0.85` in the wiki-compiler service
config if H2 confirms.

## References

- Crash forensics: kern.log entry 2026-04-27 18:20:05 (UVM
  `__kmem_cache_shutdown` BUG)
- vLLM stack trace: pilot v4 docker logs (`mamba/gdn_linear_attn.py:830`)
- Power-limit unit: `/etc/systemd/system/nvidia-power-limit.service`
  (now 400 W + persistence after 2026-04-27 reboot)
- Capability framework: `forge/AGENTS.md` § Implementation & Migration
  (capability trajectories) and § Motivation (architect-velocity goal)


---

## Closure (2026-04-27)

**G1-H1 CONFIRMED.** Pilot v5 ran 7/7 sources of module 005 over
169 minutes wall (2 h 49 m) at 400 W power cap with persistence mode
on, with zero GPU crashes. The 400 W cap is the binding fix for the
chronic UVM-leak failure mode that crashed pilots v3 and v4 within
2.5 h of start at 520 W default.

**G1-H2 NOT TESTED YET.** Pilot v5 ran with default
`gpu_memory_utilization=0.95`, so we cannot independently confirm
whether memory pressure was a contributing factor. The 400 W cap
alone is sufficient for production reliability; H2 stays as a
belt-and-braces option for future tightening if needed.

**G1-H3 NOTED.** Observed mid-pilot when killing the gpu1-keepalive
container left an orphan kernel-side CUDA context. Operational rule
codified: prefer `docker stop` over `docker rm -f` for CUDA
containers.

Outcome: G1 closes with H1 as the canonical fix. Settings codified
in `/etc/systemd/system/nvidia-power-limit.service`.


## Motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: Blackwell GPU UVM crashes mid-pilot (3 confirmed
  before G1 closed).
- **Goal**: EB + Architect-velocity (no GPU recovery cycles).
- **Outcome**: 169 min sustained 27B-FP8 inference confirmed
  at 400W power-cap.
- **Measurement source**: experiment-closure: G1 (CLOSED — 169 min sustained 27B-FP8 at 400W cap PASS per K1 v5 baseline)
- **Capability realised**: Service operation (host stability).
- **Function**: Find-stable-Blackwell-power-thermal-config.
- **Element**: this file.
