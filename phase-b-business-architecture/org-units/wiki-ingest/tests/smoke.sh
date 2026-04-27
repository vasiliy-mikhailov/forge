#!/usr/bin/env bash
# Smoke for wiki-ingest lab.
#
# Source of truth: smoke.md (this dir).
#
# What this verifies:
#   1. Containers up: jupyter-kurpatov-wiki, kurpatov-ingest,
#      kurpatov-wiki-raw-pusher, kurpatov-wiki-ingest-caddy.
#   2. GPU pinned to KURPATOV_WIKI_GPU_UUID.
#   3. torch.cuda matmul inside jupyter-kurpatov-wiki.
#   4. Caddy basic auth on $JUPYTER_KURPATOV_WIKI_DOMAIN.
#   5. ingest watcher: inotify on /workspace/sources.
#   6. raw-pusher watcher: inotify on /workspace/vault/raw/data.
#   7. Pusher image discipline: lean image, < 500 MB, distinct from GPU image.
#   8. Ingest reclaim: [reclaim] startup pass complete.

set -u
set -o pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
FORGE_ROOT=$(git -C "$HERE" rev-parse --show-toplevel)

if [[ ! -f "$FORGE_ROOT/.env" ]]; then
  echo "ERROR: $FORGE_ROOT/.env not found" >&2
  exit 2
fi
set -a; . "$FORGE_ROOT/.env"; set +a

. "$FORGE_ROOT/scripts/smoke-lib.sh"

require_env BASIC_AUTH_USER MLFLOW_TRACKING_PASSWORD \
            JUPYTER_KURPATOV_WIKI_DOMAIN KURPATOV_WIKI_GPU_UUID

# ---------- 1. containers ----------
section "containers"
for c in jupyter-kurpatov-wiki kurpatov-ingest kurpatov-wiki-raw-pusher kurpatov-wiki-ingest-caddy; do
  check_container_up "$c"
done

# ---------- 2. GPU partitioning ----------
section "GPU partitioning"
check_gpu_pinned jupyter-kurpatov-wiki "$KURPATOV_WIKI_GPU_UUID"

# ---------- 3. torch.cuda matmul ----------
section "torch.cuda matmul"
check_torch_cuda_matmul jupyter-kurpatov-wiki

# ---------- 4. Caddy basic auth ----------
section "Caddy basic auth (unauth=401, auth=200|302)"
# Plaintext basic-auth password is MLFLOW_TRACKING_PASSWORD by
# convention in this deployment (see top-level docs/architecture.md
# / caddy SPEC).
check_http_basic_auth \
  jupyter-kurpatov-wiki \
  "$JUPYTER_KURPATOV_WIKI_DOMAIN" \
  "$BASIC_AUTH_USER" \
  "$MLFLOW_TRACKING_PASSWORD" \
  "401" \
  "200|302"

# ---------- 5,6. watchers ----------
section "watchers (inotify)"
check_logs_contains \
  "ingest daemon has inotify on /workspace/sources" \
  kurpatov-ingest \
  'inotify on /workspace/sources'
check_logs_contains \
  "raw-pusher has inotify on /workspace/vault/raw/data" \
  kurpatov-wiki-raw-pusher \
  'inotify on /workspace/vault/raw/data'

# ---------- 7. pusher image discipline ----------
section "pusher image discipline"
check_container_image_differs_from \
  "raw-pusher uses a dedicated image (not the GPU image)" \
  kurpatov-wiki-raw-pusher \
  jupyter-kurpatov-wiki

# A python:3.12-slim + git + openssh-client + watchdog build is ~200 MB;
# 500 MB threshold catches a regression to FROM forge-kurpatov-wiki:latest
# (the GPU image is ~20 GB) with generous headroom.
MAX_PUSHER_BYTES=$((500 * 1024 * 1024))
check_container_image_size_below \
  "raw-pusher image size under 500MB" \
  kurpatov-wiki-raw-pusher \
  $MAX_PUSHER_BYTES

# ---------- 8. ingest startup reclaim ----------
section "ingest startup reclaim"
check_logs_contains \
  "ingest daemon ran [reclaim] startup pass on boot" \
  kurpatov-ingest \
  '\[reclaim\] startup pass complete'

summary_and_exit
