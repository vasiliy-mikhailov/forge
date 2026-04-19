# forge — architecture

This document describes how forge is physically laid out: what lives where,
how services talk to each other, how GPUs and disk are used. For "why" —
see each service's SPEC.md.

## Physical stack

- Hardware: one machine, two NVIDIA Blackwell GPUs:
  - GPU 0: `RTX PRO 6000 Workstation` (~96 GB VRAM).
  - GPU 1: `GeForce RTX 5090` (~32 GB VRAM).
- Disks:
  - SSD (system) — holds the repo, `mlflow/data/mlflow.db`, small stuff.
  - HDD pool (ZFS, `/mnt/steam`) — `/mnt/steam/forge` = `STORAGE_ROOT`,
    everything heavy lives here: models, videos, transcripts, checkpoints,
    mlflow artifacts.
- OS: Ubuntu 24.04, docker + docker compose + NVIDIA container runtime.
- GPU stack:
  - Kernel: 6.17 (HWE).
  - Driver: `nvidia-driver-590-open` (MIT/GPL kernel module). **Not the
    proprietary one, specifically `-open`** — the proprietary driver breaks
    multi-GPU on Blackwell. See
    [docs/adr/0004-nvidia-driver-open-plus-hmm-off.md](adr/0004-nvidia-driver-open-plus-hmm-off.md).
  - UVM HMM disabled via `/etc/modprobe.d/nvidia-uvm.conf`:
    `options nvidia_uvm uvm_disable_hmm=1`.
  - Container toolkit: `nvidia-container-toolkit ≥ 1.19`. We don't hand-edit
    `/etc/docker/daemon.json` — the runtime is registered via
    `nvidia-ctk runtime configure`.

## Topology

One docker network `proxy-net` (external), every service is attached:

```
                    Internet
                       │
                       ▼
                ┌────────────┐
                │   caddy    │  :80 :443 on host, ACME, basic auth
                └─────┬──────┘
                      │ proxy-net
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
 jupyter-kurpatov-wiki  jupyter-rl-2048   mlflow :5000
        │                    │               │
 kurpatov-transcriber       (same GPU)       │
 (no network, fs only)                       │
        │                                    │
        ▼  vault/raw/                        │
 kurpatov-wiki-raw-pusher                    │
 (CPU only, outbound SSH → GitHub)           │
                                              │
                    all three write metrics ▼
                                         (via caddy)
```

The kurpatov-wiki subsystem is three containers that share only the
vault filesystem — there is no code or network link between them (see
[kurpatov-wiki/docs/adr/0005-split-transcribe-and-push.md]).

## GPU ↔ service mapping

Set via variables in `.env`:

- `RL_2048_GPU_UUID` → rl-2048 (one GPU, entirely).
- `KURPATOV_WIKI_GPU_UUID` → both `jupyter-kurpatov-wiki` and
  `kurpatov-transcriber` (both share a single GPU, see
  [kurpatov-wiki/docs/adr/0003-watcher-reactive-not-cron.md]).
  `kurpatov-wiki-raw-pusher` gets no GPU — it's CPU-only.

Important: these two UUIDs must differ, otherwise the second service will
OOM.

## STORAGE_ROOT layout

```
${STORAGE_ROOT:-/mnt/steam/forge}/
├── models/                          # shared HF cache (kurpatov-wiki + rl-2048)
├── mlflow/
│   └── mlruns/                      # mlflow artifacts
├── rl-2048/
│   └── checkpoints/
└── kurpatov-wiki/
    ├── videos/                      # input mp4, structure is
    │   └── <course>/<module>/*.mp4  #   mirrored into vault/raw
    ├── vault/
    │   ├── raw/                     # RAW layer + git working tree for
    │   │   │                        #   the kurpatov-wiki-raw repo
    │   │   │                        #   (repo root IS this dir; see ADR 0005)
    │   │   ├── .git/
    │   │   ├── README.md            #   meta at the root (ADR 0005 data/
    │   │   │                        #   content-split amendment)
    │   │   └── data/                #   content subtree — transcriber and
    │   │       │                    #   pusher both default here
    │   │       └── <course>/<module>/<video_stem>/
    │   │           └── raw.json
    │   └── wiki/                    # reserved directory; the WIKI layer
    │                                #   lives in kurpatov-wiki-wiki on the
    │                                #   operator's Mac, not on the server
    │                                #   (ADR 0007). Not created by setup.
    └── checkpoints/
```

Note: `vault/` on disk is just a parent directory; the git repo lives at
`vault/raw/`, not at `vault/`. The "vault" name is legacy and kept only
to avoid rewriting `~/.ssh/kurpatov-wiki-vault` and
`vault/raw/.git/config core.sshCommand` (see ADR 0005 → Follow-ups).

Directories are created by `make setup` in the root Makefile.

## Network and public hostnames

Everything public goes through caddy, routed by hostname:

| Public hostname                     | Backend (container : port)         |
| ----------------------------------- | ---------------------------------- |
| `${JUPYTER_RL_2048_DOMAIN}`         | `jupyter-rl-2048:8888`             |
| `${JUPYTER_KURPATOV_WIKI_DOMAIN}`   | `jupyter-kurpatov-wiki:8888`       |
| `${MLFLOW_DOMAIN}`                  | `mlflow:5000`                      |

Everything is behind basic auth (`BASIC_AUTH_USER` / `BASIC_AUTH_HASH`).

## Shared conventions

- Docker compose reads variables from the root `.env` (passed through via
  `common.mk` → `--env-file ../.env`). That way every service sees the same
  `STORAGE_ROOT` and the same set of domains.
- Named volumes are used only where state needs to survive container
  recreation with minimal side effects (caddy TLS state). Everything else is
  a bind mount from `${STORAGE_ROOT}` so the path is visible and easy to
  back up.
- Image versions are pinned by tag (`caddy:2`, `mlflow:v2.14.3`, ...).
  `latest` is not used.

## Risk surfaces

- Losing the `caddy_data` volume → Let's Encrypt rate-limit on new
  certificates (mitigated by staging or waiting out the window).
- Corrupting `mlflow/data/mlflow.db` → experiment history is gone
  (artifacts survive but their metadata is lost).
- Losing `vault/raw/` → re-run every transcription (hours of audio × RTF 0.05).
  Mitigated by the `kurpatov-wiki-raw` GitHub repo: the pusher keeps it
  continuously mirrored, so a fresh `git clone` into `vault/raw/` recovers
  the transcripts without re-running whisper.
- Accidentally setting `RL_2048_GPU_UUID == KURPATOV_WIKI_GPU_UUID` → OOM.
- `apt full-upgrade` pulled in the "wrong" nvidia driver (proprietary
  instead of `-open`, or a newer major) → multi-GPU silently breaks. Run
  the post-upgrade smoke tests from `docs/operations.md` → "GPU suddenly
  unavailable".
- `nvidia_uvm` loaded without `uvm_disable_hmm=1` (for example, someone
  deleted `/etc/modprobe.d/nvidia-uvm.conf` during reprovisioning) → CUDA
  operations hang or crash. That's exactly what ADR 0004 is about.
