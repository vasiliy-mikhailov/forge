# forge — operations / runbook

Collection of practical procedures: how to fix, how to back up, how to
migrate.

## GPU host setup (read first — this is part of disaster recovery!)

On a fresh machine with two NVIDIA Blackwell cards (RTX PRO 6000 Workstation
+ RTX 5090) CUDA does not work out of the box either with the proprietary
driver or with default HMM settings. The reasons and details are in
[docs/adr/0004-nvidia-driver-open-plus-hmm-off.md](adr/0004-nvidia-driver-open-plus-hmm-off.md).
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

# 3. Bring up the base — caddy will issue TLS via ACME
make base

# 4. Add videos (for kurpatov-wiki) under
#    ${STORAGE_ROOT}/kurpatov-wiki/videos/<course>/<module>/*.mp4
# and bring up the GPU services:
make kurpatov-wiki
make rl-2048
```

## Rebuilding a single service image

After changing a Dockerfile:

```bash
make <service>-down
make <service>-build
make <service>
make <service>-logs   # verify it came up cleanly
```

Note for kurpatov-wiki: its `docker-compose.yml` uses the same
`image: forge-kurpatov-wiki:latest` for the jupyter and transcriber services.
Building from either rebuilds the shared image.

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
2. `${STORAGE_ROOT}/kurpatov-wiki/videos/` — sources (separate from the repo).
3. `${STORAGE_ROOT}/kurpatov-wiki/vault/raw/` — transcription results
   (expensive to regenerate).
4. `mlflow/data/mlflow.db` + `${STORAGE_ROOT}/mlflow/mlruns/` — experiment
   history.
5. `${STORAGE_ROOT}/kurpatov-wiki/checkpoints/`,
   `${STORAGE_ROOT}/rl-2048/checkpoints/` — training checkpoints.

What NOT to back up:

- `${STORAGE_ROOT}/models/` — it's an HF cache, always refetchable.
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
   - `vault/raw/` (mandatory — otherwise transcribe starts from zero).
   - `videos/` (if you want them as the source of truth).
   - `mlflow/data/mlflow.db` and `mlruns/` (if you want history).
5. `make setup && make base && make kurpatov-wiki && make rl-2048`.

Health check:

```bash
make ps
make smoke                                        # full end-to-end smoke suite
make kurpatov-wiki-logs | head -50
```

## End-to-end smoke test

`make smoke` (or `./scripts/smoke.sh`) runs an idempotent, read-only
health check across the whole stack. What it verifies:

1. All 5 containers Up: `caddy`, `mlflow`, `jupyter-rl-2048`,
   `jupyter-kurpatov-wiki`, `kurpatov-transcriber`.
2. GPU partitioning — `jupyter-rl-2048` sees exactly the GPU pinned by
   `RL_2048_GPU_UUID` and `jupyter-kurpatov-wiki` sees the one pinned by
   `KURPATOV_WIKI_GPU_UUID`.
3. `torch.cuda` is available inside both GPU containers and a small
   1024×1024 matmul completes without error.
4. Caddy: each of the three domains returns `401` unauthenticated and
   `200` (mlflow) or `302` (jupyter, redirects to `/lab`) with basic auth.
5. mlflow REST API (`/api/2.0/mlflow/experiments/search`) returns JSON
   containing an experiments list.
6. `kurpatov-transcriber` has logged `inotify on /workspace/videos` —
   the reactive watcher has started.

Exit code is `0` iff all checks pass. Run it after `make base` +
`make rl-2048` + `make kurpatov-wiki`, after any service rebuild, and
as a quick periodic sanity check.

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

Full runbook: [docs/adr/0004-nvidia-driver-open-plus-hmm-off.md](adr/0004-nvidia-driver-open-plus-hmm-off.md).

## Rotating GPUs between services

If you need to hand the full 5090 to rl-2048 temporarily:

```bash
make stop-gpu
# edit .env: RL_2048_GPU_UUID=${GPU_RTX5090_UUID}
make rl-2048
# to swap back — put the UUIDs back and repeat.
```

## Transcript migration

If the directory layout under `vault/raw/` changes, there's a migration
script at `kurpatov-wiki/notebooks/migrate_vault_hierarchy.py`. Run it from
inside the container (raw files are root-owned):

```bash
docker exec jupyter-kurpatov-wiki \
  python3 /workspace/notebooks/migrate_vault_hierarchy.py \
    --vault-raw /workspace/vault/raw \
    --strip-prefix /workspace/videos \
    --dry-run
# verify the plan → remove --dry-run
```
