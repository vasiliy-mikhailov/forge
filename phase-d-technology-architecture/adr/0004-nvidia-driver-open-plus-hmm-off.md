# ADR 0004 — nvidia-driver-590-open + uvm_disable_hmm=1

## Status
Accepted (2026-04-19). Paid for in many hours of debugging. Do not revert
without a very good reason.

## Context
The machine has two GPUs:

- GPU 0: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition` (~96 GB VRAM).
- GPU 1: `NVIDIA GeForce RTX 5090` (~32 GB VRAM).

Both are Blackwell (sm_120). At the time of this ADR the stable NVIDIA
Linux branch is 590.x.

We hit two independent issues that **show up together**, which makes them
easy to confuse:

1. **Proprietary `nvidia-driver-590` fails to see one of the cards / fails
   `cuInit`.** On kernel 6.17 + Blackwell, only the `*-open` variant works
   (MIT/GPL kernel module, proprietary user-space). This is what NVIDIA
   itself recommends for all Turing+ cards starting from driver 560. The
   proprietary-branch symptom: `nvidia-smi` lists both GPUs, but `cuInit(0)`
   in Python returns an error on one of them (or both, depending on the
   driver version).

2. **UVM HMM breaks on multi-GPU + Blackwell.** Symptom: the container
   starts, `nvidia-smi` inside sees both cards, but any torch run on one
   of them hangs or fails with a CUDA error on the first operation.
   `dmesg` shows complaints from `nvidia_uvm`. Fix: disable HMM.

Cost of getting it wrong: hours. Reinstalling a driver takes ~10 minutes,
but figuring out that you need **specifically `-open`** and
**specifically `uvm_disable_hmm=1`** required cycling through both driver
packages and several kernel parameters.

## Decision

### Driver
Use `nvidia-driver-590-open` (with DKMS). Check:

```bash
dpkg -l | grep -E 'nvidia-(driver|dkms)-590'
# expected:
# ii nvidia-driver-590-open  590.48.01-...
# ii nvidia-dkms-590-open    590.48.01-...
```

### UVM parameters
`/etc/modprobe.d/nvidia-uvm.conf`:

```
options nvidia_uvm uvm_disable_hmm=1
```

Runtime check (after reboot):

```bash
cat /sys/module/nvidia_uvm/parameters/uvm_disable_hmm   # must be Y
```

### Container toolkit
`nvidia-container-toolkit` ≥ 1.19.0. The docker runtime config lives in
`/etc/nvidia-container-runtime/config.toml` — don't hand-edit
`/etc/docker/daemon.json`:

```bash
sudo apt install nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## Consequences
- Plus: both GPUs work reliably, shared between containers by UUID.
- Plus: `-open` gets updates at NVIDIA's pace and is more compatible with
  new kernels.
- Plus: the fix is declarative — it survives reboot because it lives in
  modprobe.d.
- Minus: requires an explicit post-install step (modprobe.d + reboot).
  This is documented in `phase-g-implementation-governance/operations.md` → "GPU host setup".
- Minus: HMM is off → some CUDA managed-memory flows might behave
  unexpectedly. Within forge we haven't seen it bite (whisper + vllm +
  unsloth all work).

## Completeness smoke test
Should pass **without sudo**, from a regular user:

```bash
nvidia-smi -L
# GPU 0: NVIDIA RTX PRO 6000 Blackwell ... (UUID: GPU-...)
# GPU 1: NVIDIA GeForce RTX 5090 ... (UUID: GPU-...)

docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu24.04 nvidia-smi
# same table, but from inside a container

# cuInit must return 0 on both cards:
for d in 0 1; do
  echo "--- GPU $d ---"
  CUDA_VISIBLE_DEVICES=$d python3 -c "
import ctypes
lib = ctypes.CDLL('libcuda.so.1')
print('cuInit =', lib.cuInit(0))"
done
```

If `cuInit` returns non-zero, that is exactly the bug this ADR is about.
Check in order:

1. `modinfo nvidia | grep license` — must be `Dual MIT/GPL` (open variant).
2. `cat /sys/module/nvidia_uvm/parameters/uvm_disable_hmm` — must be `Y`.
3. `sudo dmesg | grep -iE 'nvidia|nvrm' | tail -40` — no fresh errors.

## Rejected
- **Proprietary `nvidia-driver-590`** (without `-open`). Did not run stably
  on kernel 6.17 + Blackwell.
- **Leaving UVM alone.** Multi-GPU flows crashed, see Context.
- **Moving to one of the `-server` driver variants.** Target scenario is a
  workstation, not a headless server; `*-server` variants weren't tested.


## Measurable motivation chain (OKRs)
Per [P7](../../phase-preliminary/architecture-principles.md) — backfit:

- **Driver**: nvidia driver mode + HMM setting affects GPU
  stability under sustained 27B inference (G1 finding).
- **Goal**: Service operation (sustained GPU stability).
- **Outcome**: open driver + HMM off; G1's 169-min sustained
  pilot validated.
- **Measurement source**: audit-predicate: P4 (single-server invariant; nvidia-smi smoke check)
