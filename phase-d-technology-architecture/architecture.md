# forge — architecture

How forge is physically laid out: what lives where, how services talk
to each other, how GPUs and disk are used. For "why" — see each lab's
`SPEC.md` and the relevant ADR.

After [ADR 0007](../adr/0007-labs-restructure-self-contained-caddy.md)
forge is organized as **labs** under `labs/<lab>/`, each lab fully
self-contained (own caddy, compose, SPEC, ADRs). Labs are **mutex on
host ports :80/:443** because each lab's caddy binds them. Bench is
the one exception: it has no caddy and is co-runnable with the
compiler lab.

## Physical stack

- Hardware: one machine, two NVIDIA Blackwell GPUs:
  - GPU 0: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition` (~96 GB VRAM).
  - GPU 1: `NVIDIA GeForce RTX 5090` (~32 GB VRAM).
- Disks:
  - SSD (system) — holds the repo and small stuff.
  - HDD pool (ZFS, `/mnt/steam`) — `/mnt/steam/forge` = `STORAGE_ROOT`,
    everything heavy lives here: model weights cache, sources,
    transcripts, checkpoints, mlflow artifacts, bench experiments.
- OS: Ubuntu 24.04, docker + docker compose + NVIDIA container runtime.
- GPU stack:
  - Kernel: 6.17 (HWE).
  - Driver: `nvidia-driver-590-open` (MIT/GPL kernel module). **Not the
    proprietary one, specifically `-open`** — proprietary breaks
    multi-GPU on Blackwell. See
    [adr/0004-nvidia-driver-open-plus-hmm-off.md](../adr/0004-nvidia-driver-open-plus-hmm-off.md).
  - UVM HMM disabled via `/etc/modprobe.d/nvidia-uvm.conf`:
    `options nvidia_uvm uvm_disable_hmm=1`.
  - Container toolkit: `nvidia-container-toolkit ≥ 1.19`. We don't
    hand-edit `/etc/docker/daemon.json` — runtime is registered via
    `nvidia-ctk runtime configure`.

## Topology (per-lab caddy after ADR 0007)

Each lab owns its own caddy, attached to the shared `proxy-net`
docker network. Only one caddy at a time can hold host :80/:443.

```
                              Internet
                                  │
                                  ▼
                  ┌───────── exactly one of ─────────┐
                  │                                  │
        kurpatov-wiki-compiler-caddy        rl-2048-caddy
                  │                                  │
        ╭─────────┼─────────╮            ╭───────────┼───────────╮
        │ proxy-net          │            │ proxy-net              │
        ▼                                 ▼           ▼
   vllm-inference                    jupyter-rl-2048   mlflow:5000
   :8000  (Bearer auth, no caddy basic auth — ADR 0005)

                  │                                  │
                  └─────────── or ───────────────────┘
                                  │
                                  ▼
                       kurpatov-wiki-ingest-caddy
                                  │
              ╭───────────────────┼───────────────────╮
              │ proxy-net (jupyter only)                        │
              ▼
         jupyter-kurpatov-wiki

         (kurpatov-ingest, kurpatov-wiki-raw-pusher run alongside
          on the host but bind no public ports — fs-only and SSH-out
          to GitHub)
```

Bench (`phase-b-business-architecture/org-units/kurpatov-wiki-bench/`) launches one short-lived sandboxed
container per `make bench` invocation. It has no caddy, attaches to
docker `bridge`, and reaches the compiler over the public TLS endpoint.

## Lab inventory

| Lab                                | Containers (per-lab caddy + workers)                                                                                                                  | GPU                                  | Caddy hosts                          |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------ |
| `phase-b-business-architecture/org-units/kurpatov-wiki-compiler/`     | `kurpatov-wiki-compiler-caddy`, `vllm-inference`                                                                                                      | `INFERENCE_GPU_UUID` (Blackwell)     | `${INFERENCE_DOMAIN}`                 |
| `phase-b-business-architecture/org-units/kurpatov-wiki-ingest/`       | `kurpatov-wiki-ingest-caddy`, `jupyter-kurpatov-wiki`, `kurpatov-ingest`, `kurpatov-wiki-raw-pusher`                                                   | `KURPATOV_WIKI_GPU_UUID` (5090)      | `${JUPYTER_KURPATOV_WIKI_DOMAIN}`     |
| `phase-b-business-architecture/org-units/kurpatov-wiki-bench/`        | one-shot `bench-<run_id>`                                                                                                                             | none (CPU only)                      | none                                 |
| `phase-b-business-architecture/org-units/rl-2048/`                    | `rl-2048-caddy`, `jupyter-rl-2048`, `mlflow`                                                                                                          | `RL_2048_GPU_UUID` (Blackwell)       | `${MLFLOW_DOMAIN}`, `${JUPYTER_RL_2048_DOMAIN}` |

## GPU ↔ lab mapping

Set via `.env`:

- `RL_2048_GPU_UUID` → `jupyter-rl-2048`. Default: Blackwell.
- `KURPATOV_WIKI_GPU_UUID` → both `jupyter-kurpatov-wiki` and
  `kurpatov-ingest` (they share one GPU per
  [phase-b-business-architecture/org-units/kurpatov-wiki-ingest/docs/adr/0003-watcher-reactive-not-cron.md](../labs/kurpatov-wiki-ingest/docs/adr/0003-watcher-reactive-not-cron.md)).
  Default: RTX 5090. `kurpatov-wiki-raw-pusher` is CPU-only (per
  [phase-b-business-architecture/org-units/kurpatov-wiki-ingest/docs/adr/0006-lean-pusher-image.md](../labs/kurpatov-wiki-ingest/docs/adr/0006-lean-pusher-image.md)).
- `INFERENCE_GPU_UUID` → `vllm-inference`. Default: Blackwell.

**Mutex consequences:** Blackwell hosts compiler OR rl-2048 (not both
simultaneously). Going to dual-GPU TP on the compiler will eventually
take both cards, locking out kurpatov-wiki-ingest as well.

## STORAGE_ROOT layout

```
${STORAGE_ROOT:-/mnt/steam/forge}/
├── shared/
│   └── models/                        # HF cache, shared by every lab
│                                       # mounted into vLLM, jupyter-*,
│                                       # bench (read-only public weights)
└── labs/
    ├── kurpatov-wiki-compiler/
    │   ├── caddy-data/                # per-lab caddy TLS state
    │   └── caddy-config/
    ├── kurpatov-wiki-ingest/
    │   ├── sources/                   # input media (audio, video, HTML, PDF)
    │   │   └── <course>/<module>/*.<ext>
    │   ├── vault/
    │   │   └── raw/                   # RAW layer + git working tree for
    │   │       │                      #   the kurpatov-wiki-raw repo
    │   │       │                      #   (repo root IS this dir; ADR 0005)
    │   │       ├── .git/
    │   │       ├── README.md
    │   │       └── data/              # content subtree — ingest daemon
    │   │           └── <course>/<module>/<stem>/
    │   │               └── raw.json   # <stem> = source filename
    │   │                              #         minus extension (ADR 0008)
    │   ├── checkpoints/
    │   ├── caddy-data/
    │   └── caddy-config/
    ├── kurpatov-wiki-bench/
    │   └── experiments/<run_id>/      # per-experiment artifacts
    │       ├── events.jsonl           #   (one experiment = one agent run)
    │       ├── summary.json
    │       └── vllm-snapshot-{start,end}.json
    │   └── evals/                     # T1 microbench CSVs
    │       └── microbench/<date>-<exp_id>-<model>.csv
    └── rl-2048/
        ├── checkpoints/
        ├── mlruns/                    # mlflow artifacts (lab-local)
        ├── mlflow/data/               # mlflow.db
        ├── caddy-data/
        └── caddy-config/
```

`make setup` creates this skeleton (root Makefile).

The "vault" name is legacy; the git repo lives at `vault/raw/`, not at
`vault/`. Kept to avoid rewriting `~/.ssh/kurpatov-wiki-vault` and
`vault/raw/.git/config core.sshCommand` (see ADR 0005 → Follow-ups in
the ingest lab).

## Network and public hostnames

Every public-facing surface goes through a per-lab caddy attached to
`proxy-net`. The active lab's caddy binds host :80/:443.

| Public hostname                     | Active when lab is up                  | Backend                      |
| ----------------------------------- | -------------------------------------- | ---------------------------- |
| `${INFERENCE_DOMAIN}`               | `kurpatov-wiki-compiler`               | `vllm-inference:8000`        |
| `${JUPYTER_KURPATOV_WIKI_DOMAIN}`   | `kurpatov-wiki-ingest`                 | `jupyter-kurpatov-wiki:8888` |
| `${JUPYTER_RL_2048_DOMAIN}`         | `rl-2048`                              | `jupyter-rl-2048:8888`       |
| `${MLFLOW_DOMAIN}`                  | `rl-2048` (mlflow lives inside rl-2048 per ADR 0007) | `mlflow:5000`                |

Auth: jupyter-* and mlflow are behind caddy basic auth
(`BASIC_AUTH_USER` / `BASIC_AUTH_HASH`); the inference endpoint is
the documented exception (vLLM Bearer auth, see
[ADR 0005](../adr/0005-inference-subsystem.md)). TLS terminates at caddy
in every case.

## Shared conventions

- Compose reads variables from the root `.env` (find via
  `git rev-parse --show-toplevel` in `common.mk`, so it works at any
  nesting depth — including from per-lab `caddy/`/`mlflow/` sublabs).
- Bind mounts to `${STORAGE_ROOT}/...` everywhere except caddy TLS state
  (the only real named-volume use; everything else is a visible path
  for backups).
- Image versions are pinned by tag (`caddy:2`, `mlflow:v2.14.3`,
  `vllm/vllm-openai:v0.19.1-cu130-ubuntu2404`, …). `latest` is not used.

## Risk surfaces

- Losing per-lab `caddy-data/` → Let's Encrypt rate-limit on new certs
  (mitigated by staging or waiting out the window).
- Corrupting `${STORAGE_ROOT}/labs/rl-2048/mlflow/data/mlflow.db` →
  experiment metadata is gone (mlruns/ artifacts survive).
- Losing `${STORAGE_ROOT}/labs/kurpatov-wiki-ingest/vault/raw/` →
  re-run every transcription (hours of audio × RTF 0.05). Mitigated
  by the `kurpatov-wiki-raw` GitHub repo (continuous mirror via the
  pusher).
- `RL_2048_GPU_UUID == KURPATOV_WIKI_GPU_UUID == INFERENCE_GPU_UUID` —
  any overlap → OOM on the second container.
- `apt full-upgrade` pulled in the wrong nvidia driver (proprietary
  instead of `-open`, or a newer major) → multi-GPU silently breaks.
  Diagnostics: [`phase-g-implementation-governance/operations.md`](../phase-g-implementation-governance/operations.md) → "GPU suddenly
  unavailable".
- `nvidia_uvm` loaded without `uvm_disable_hmm=1` → CUDA hangs.
  See [ADR 0004](../adr/0004-nvidia-driver-open-plus-hmm-off.md).
- Two labs' caddies up at once → host port conflict; the second one
  fails to bind. Smoke dispatcher catches this:
  `make smoke` exits 1 with a "broken mutex" message.
