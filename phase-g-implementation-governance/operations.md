# forge — operations / runbook

Collection of practical procedures: how to fix, how to back up, how to
migrate.

## Quick start

For an architect who already has the host set up. First-time setup is
in "GPU host setup" below.

Fill `.env` from the template:

```bash
cp .env.example .env
# Fill in ACME_EMAIL, BASIC_AUTH_HASH (see comment in .env.example),
# domains, and GPU UUIDs (nvidia-smi -L).
```

Create on-disk layout (creates `` and subdirs):

```bash
make setup
```

Bring up one lab. Labs are mutex on host :80/:443; only one at a
time, except `wiki-bench` may co-run with `wiki-compiler` (bench
is a client without a caddy):

```bash
make wiki-compiler   # vLLM endpoint
make wiki-ingest     # whisper + ingest
make rl-2048         # GRPO sandbox
```

Diagnostics:

```bash
make ps    # containers
make gpu   # GPU load
make du    # on-disk sizes under STORAGE_ROOT
```

## Useful commands for the agent

- Service logs: `make <lab>-logs` (tail -f of `docker logs <container>`).
- Enter a container: `docker exec -it <container> bash`.

## GPU host setup (read first — this is part of disaster recovery!)

On a fresh machine with two NVIDIA Blackwell cards (RTX PRO 6000 Workstation
+ RTX 5090) CUDA does not work out of the box either with the proprietary
driver or with default HMM settings. The reasons and details are in
[phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md](../phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md).
The one-time setup on a fresh Ubuntu 24.04:

```bash
# 1. Remove the proprietary nvidia driver if it is installed.
sudo apt purge -y 'nvidia-driver-*' 'nvidia-dkms-*' 'nvidia-kernel-*'

# 2. Install the open variant (MIT/GPL kernel module, proprietary user-space).
sudo apt install -y nvidia-driver-590-open

# 3. Disable UVM HMM (without this multi-GPU crashes on Blackwell).
echo "options nvidia_uvm uvm_disable_hmm=1" \
  | sudo tee /etc/modprobe.d/nvidia-uvm.conf

# 4. Install the container toolkit and wire it into docker.
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker

# 5. Reboot (the nvidia_uvm module only picks up parameters after reboot).
sudo reboot
```

After reboot, smoke test:

```bash
nvidia-smi -L                                          # both GPUs visible
cat /sys/module/nvidia_uvm/parameters/uvm_disable_hmm  # Y
modinfo nvidia | grep ^license                         # Dual MIT/GPL
docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu24.04 nvidia-smi
# cuInit on both cards from Python:
for d in 0 1; do
  echo "--- GPU $d ---"
  CUDA_VISIBLE_DEVICES=$d python3 -c "
import ctypes
lib = ctypes.CDLL('libcuda.so.1')
print('cuInit =', lib.cuInit(0))"
done
# cuInit must return 0 on both. If not — read ADR 0004.
```

**Typical symptoms if this step is skipped:**

- `nvidia-smi` works, but `docker run --gpus all ... nvidia-smi` fails.
- The container starts, jupyter sees the GPU, but the first torch
  operation hangs or returns `CUDA error: unknown error`.
- `cuInit(0)` returns nonzero on one of the cards.
- `dmesg` shows `nvidia_uvm` warnings/errors after the container starts.

Continue below only after the smoke test passes on both GPUs.

## Bootstrap from scratch (fresh server)

Host prerequisites: **GPU host setup above is done**, docker, docker compose,
NVIDIA container runtime, ports 80/443 free, a ZFS/ext4 pool with enough
headroom.

```bash
git clone https://github.com/vasiliy-mikhailov/forge.git
cd forge

# 1. Fill in .env
cp .env.example .env
$EDITOR .env
# required: ACME_EMAIL, BASIC_AUTH_HASH, *_DOMAIN, *_GPU_UUID.
# bcrypt hash for basic auth:
#   docker run --rm caddy:2 caddy hash-password --plaintext '<password>'
# GPU UUIDs:
#   nvidia-smi -L

# 2. Directories on the big disk
sudo mkdir -p /mnt/steam/forge
sudo chown -R $USER:$USER /mnt/steam/forge
make setup

# 3. Bring up one lab (labs are mutex on host :80/:443).
make wiki-ingest    # transcription pipeline (Whisper + watchers + git pusher)
# or:
# make wiki-compiler  # vLLM serving (compiles raw → wiki via LLM)
# or:
# make rl-2048                 # GRPO sandbox + jupyter + mlflow
# Bench is co-runnable with compiler:
# make wiki-compiler && make -C phase-c-information-systems-architecture/application-architecture/wiki-bench bench

# 4. Add source media for wiki-ingest under
#    ${STORAGE_ROOT}/labs/wiki-ingest/sources/<course>/<module>/*.<ext>
#    (extensions: see INGEST_EXTENSIONS in
#    phase-c-information-systems-architecture/application-architecture/wiki-ingest/notebooks/0{2,3}_*_ingest*.py)
```

## Rebuilding a single service image

After changing a Dockerfile:

```bash
make <service>-down
make <service>-build
make <service>
make <service>-logs   # verify it came up cleanly
```

Note for kurpatov-wiki: its `docker-compose.yml` builds **two** images.
`jupyter-kurpatov-wiki` and `kurpatov-ingest` share the GPU image
`forge-kurpatov-wiki:latest` (built from `Dockerfile`, ~20 GB,
CUDA + torch + whisper + jupyter). `kurpatov-wiki-raw-pusher` runs a
dedicated lean image `forge-kurpatov-wiki-pusher:latest` built from
`Dockerfile.pusher` (`python:3.12-slim` + git + openssh-client +
watchdog, ~200 MB). `make kurpatov-wiki-ingest-build` runs
`docker compose build` which walks every service with a `build:`
block, so both images rebuild together — no per-image target is
needed. See
[phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md](../phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md)
and
[phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0006-lean-pusher-image.md](../phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0006-lean-pusher-image.md).

### Pinned-core build (keeps ssh responsive)

Cold builds saturate every core — ssh/mlflow/arbitrage become unusable
for 10-20 min. Fix: a dedicated buildx builder (`slowbuilder`) pinned to
CPU 0 only. `common.mk`'s `build` target auto-provisions this builder
on first invocation and routes every `make *-build` through it via
`BUILDX_BUILDER=slowbuilder`. Builds take longer wall-clock but the
other 23 cores stay free.

Verify the pin:

```bash
docker inspect buildx_buildkit_slowbuilder0 \
  --format 'cpuset={{.HostConfig.CpusetCpus}} restart={{.HostConfig.RestartPolicy.Name}}'
# cpuset=0 restart=unless-stopped
```

To rebuild full-speed on all cores temporarily (e.g. a one-off you want
done fast): `BUILDX_BUILDER=default make <service>-build`.

To wipe the builder (rare — after a botched docker upgrade or if its
cache gets stuck): `docker buildx rm slowbuilder && docker rm -f
buildx_buildkit_slowbuilder0`. Next `make *-build` recreates it.

## Logs

```bash
make <service>-logs          # tail -f the service container
docker logs --since=1h <container>  # last hour
```

## GPU / disk

```bash
make gpu                     # load + memory per GPU
make du                      # what is using space under STORAGE_ROOT
nvidia-smi                   # full snapshot
nvidia-smi -L                # UUIDs
```

## Backups

What to back up, in order of priority:

1. `.env` — secrets. Keep in a password manager, not in git.
2. `${STORAGE_ROOT}/labs/wiki-ingest/sources/` — input media (separate from the repo).
3. `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/` — transcription results
   (expensive to regenerate). Also continuously mirrored to the
   `kurpatov-wiki-raw` private GitHub repo by the
   `kurpatov-wiki-raw-pusher` container, so in practice a fresh
   `git clone` recovers this layer without re-running whisper (see
   [phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md](../phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md)).
4. `${STORAGE_ROOT}/labs/rl-2048/mlflow/data/mlflow.db` + `${STORAGE_ROOT}/labs/rl-2048/mlruns/` — experiment
   history.
5. `${STORAGE_ROOT}/labs/wiki-ingest/checkpoints/`,
   `${STORAGE_ROOT}/labs/rl-2048/checkpoints/` — training checkpoints.

What NOT to back up:

- `${STORAGE_ROOT}/shared/models/` — it's an HF cache, always refetchable.
- `caddy_data` / `caddy_config` — TLS state; losing it means a fresh ACME
  cycle which can hit rate limits but otherwise no downtime.
- `.inductor_cache`, `.triton_cache`, `.vllm_cache` inside containers —
  regenerated on demand.

## Disaster recovery

Order:

1. Fresh server, docker + NVIDIA runtime ready.
2. `git clone` the repo.
3. Drop `.env` from the password manager.
4. Create `STORAGE_ROOT`, restore from backups:
   - `vault/raw/` (mandatory — otherwise ingest starts from zero).
     Fastest path: `git clone git@github.com:vasiliy-mikhailov/kurpatov-wiki-raw.git`
     into `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw`, then configure
     `.git/config core.sshCommand` to use the `~/.ssh/kurpatov-wiki-vault`
     deploy key so the pusher can resume from the server (ADR 0005).
   - `sources/` (if you want them as the source of truth).
   - `mlflow/data/mlflow.db` and `mlruns/` (if you want history).
5. `make setup`, then `make <lab>` for whichever lab you want to bring up first (labs are mutex on host :80/:443).

Health check:

```bash
make ps
make smoke                                        # full end-to-end smoke suite
make kurpatov-wiki-logs | head -50
```

## End-to-end smoke test

`make smoke` is now a **dispatcher** (after [ADR 0007](adr/0007-labs-restructure-self-contained-caddy.md)
labs are mutex on host :80/:443, so smoke is per-lab). The dispatcher
detects which lab's caddy is currently running and delegates to that
lab's `tests/smoke.sh`; multiple caddies up = exit 1 (broken mutex);
no lab up = exit 2.

Full dispatcher contract: [`tests/smoke.md`](../tests/smoke.md).
Per-lab smoke models: [`<lab>/tests/smoke.md`](../phase-c-information-systems-architecture/application-architecture/).
Shared assertion helpers: [`scripts/smoke-lib.sh`](../scripts/smoke-lib.sh).
Coverage map and TDD loop: [`tests/README.md`](../tests/README.md).

What is verified per lab is documented in each lab's `tests/smoke.md`. The compiler lab asserts vLLM healthy + caddy up + correct served model on `/v1/models`; ingest asserts the four pipeline containers + GPU pinning + watchers + pusher image discipline; rl-2048 asserts jupyter + mlflow + caddy + REST API; bench (invoked separately via `make -C phase-c-information-systems-architecture/application-architecture/wiki-bench smoke`) asserts the openhands binary + image build + gh auth + compiler endpoint reachable.

Exit code is `0` iff all checks pass. Run it after bringing one lab up (`make <lab>`; bench co-runs with compiler), after any rebuild, and as a periodic sanity check.

The plaintext basic-auth password is read from `MLFLOW_TRACKING_PASSWORD`
in `.env` — by convention in this deployment the same secret is used
for Caddy basicauth and the mlflow tracking client.

## GPU suddenly unavailable

Symptoms: `docker run --gpus all ...` fails, `nvidia-smi` inside the
container doesn't see the card, or torch returns `CUDA error`. Quick
checklist:

```bash
# 1. Does the host see both cards?
nvidia-smi -L

# 2. Driver license and version haven't changed (e.g. after apt upgrade)?
modinfo nvidia | grep -E '^(license|version)'
# license: Dual MIT/GPL   ← required
# version: 590.48.01      ← if major changed, re-read ADR 0004

# 3. UVM still has HMM off?
cat /sys/module/nvidia_uvm/parameters/uvm_disable_hmm
# Y   ← required

# 4. Dev nodes in place?
ls -la /dev/nvidia*          # /dev/nvidia0, /dev/nvidia1, /dev/nvidia-uvm*
# If /dev/nvidia-uvm is missing, help the module come up:
sudo modprobe nvidia_uvm
sudo nvidia-modprobe -u -c=0

# 5. No fresh errors in dmesg?
sudo dmesg -T | grep -iE 'nvidia|nvrm' | tail -40

# 6. Container tooling alive?
docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu24.04 nvidia-smi
# If only this fails — reconfigure the runtime:
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

If apt pulled in the wrong driver flavor (installs `nvidia-driver-590`
instead of `-open`, or jumped to 595+) — reinstall
`nvidia-driver-590-open` and reboot. This is rare, but happens after
`apt full-upgrade` on a neglected machine.

Full runbook: [phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md](../phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md).

## Rotating GPUs between services

If you need to hand the full 5090 to rl-2048 temporarily:

```bash
make stop-all
# edit .env: RL_2048_GPU_UUID=${GPU_RTX5090_UUID}
make rl-2048
# to swap back — put the UUIDs back and repeat.
```

## Pushing new source media from laptop

Drop new lecture files into `~/Downloads/Курпатов/` on the laptop and
ship them to the server with a single command:

```bash
make push-sources
```

This moves every media file (any suffix in the INGEST_EXTENSIONS allow-list
— video: `mp4/mkv/webm/mov/m4v/avi`, audio: `mp3/m4a/wav/ogg/flac/opus/aac`,
html: `html/htm`)
from the source folder to the current default module under
`${STORAGE_ROOT}/labs/wiki-ingest/sources/` on the server, deleting each file locally only
after the transfer is verified. The `kurpatov-ingest` daemon picks
them up via inotify and ingests within ~10s of each file landing —
no server-side action required. faster-whisper handles audio natively via
ffmpeg, so `.mp3` and friends go through the same path as `.mp4`.
HTML files (`.html`, `.htm` — typically getcourse.ru lesson exports)
take the HTML-extractor path instead, producing the same segments[]
shape minus timing — see
[phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0008-ingest-dispatch.md](../phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0008-ingest-dispatch.md).

Defaults live in `scripts/push-sources.sh` and are currently:

- `SRC     = ~/Downloads/Курпатов`
- `HOST    = 192.168.0.2` (LAN; set to `mikhailov.tech` for VPN)
- `PORT    = 22` (set to `2222` for VPN)
- `COURSE  = Психолог-консультант`
- `MODULE  = 005 Природа внутренних конфликтов. Базовые психологические потребности`

Override via env vars for a one-off (e.g. a different module):

```bash
MODULE='006 <next module name>' make push-sources
SRC=~/somewhere/else make push-sources
HOST=mikhailov.tech PORT=2222 make push-sources   # over VPN instead of LAN
```

Dry-run first if you want to check what will move:

```bash
bash scripts/push-sources.sh --dry-run
```

When the "current module" changes (you finish uploading 005 and move
on to 006), edit the `MODULE` default in `scripts/push-sources.sh` and
commit the change — the repo is the source of truth for the active
module.

Requires GNU rsync 3.x on the laptop. macOS ships `openrsync` by
default, which lacks `-s` and `--append-verify`; fix once with
`brew install rsync` and ensure `/opt/homebrew/bin` is ahead of
`/usr/bin` in `PATH`.

## Transcript migration

If the directory layout under `vault/raw/` changes, there's a migration
script at `phase-c-information-systems-architecture/application-architecture/wiki-ingest/notebooks/migrate_vault_hierarchy.py`. Run it from
inside the container (raw files are root-owned):

```bash
docker exec jupyter-kurpatov-wiki \
  python3 /workspace/notebooks/migrate_vault_hierarchy.py \
    --vault-raw /workspace/vault/raw \
    --strip-prefix /workspace/sources \
    --dry-run
# verify the plan → remove --dry-run
```


## Operational log

Chronological log of host-level actions per the
[DevOps role](../phase-b-business-architecture/roles/devops.md).
Format: `- YYYY-MM-DD <action> — <ADR / R-NN cited> — <outcome>`.
Newest entries above oldest.

- 2026-05-02 bootstrap — ADR 0007 + ADR 0014 — operational log
  appendix opened. The runbook above documents *how to* operate;
  this section logs *when* an operational action ran. Audited by
  DO-02 (dated entries) + DO-03 (every governing-keyword
  paragraph cites an ADR or R-NN). Pre-existing runbook content
  stays untouched.


## Motivation chain

Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: services on a single host (P4) need a runbook +
  a chronological log.
- **Goal**: Architect-velocity (ops actions logged + reversible).
- **Outcome**: this file is the runbook (procedural) + the
  Operational log (chronological, append-only); DevOps role
  appends to the log per audit-2026-05-01l F3.
- **Capability realised**: Service operation.
- **Function**: Operate-host-procedures + log-actions.
- **Element**: this file.
