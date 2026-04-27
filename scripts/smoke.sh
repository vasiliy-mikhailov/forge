#!/usr/bin/env bash
# forge smoke dispatcher.
#
# After the labs/ refactor (ADR 0007), labs are mutex on host ports
# 80/443 — only one lab's caddy can be running at a time. Smoke is
# therefore per-lab: this script just figures out which lab is active
# and delegates to its `tests/smoke.sh`.
#
# Bench is a one-shot client of compiler, not a service; its smoke
# (image built, openhands binary present, etc.) is invoked separately
# via `make -C phase-b-business-architecture/org-units/kurpatov-wiki-bench smoke` and bundled into the
# compiler's smoke when bench is co-running with compiler.
#
# Usage:
#   make smoke              # from forge root (recommended)
#   ./scripts/smoke.sh      # direct
#
# Exit:
#   0  — active lab's smoke passed.
#   1  — active lab's smoke had failures, OR multiple labs caddy is up
#        (broken mutex invariant).
#   2  — no lab is active (no service-lab caddy is running).

set -u
set -o pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/.." &>/dev/null && pwd)

# Map: caddy container name → lab dir (relative to forge root).
declare -A LAB_OF_CADDY=(
  [kurpatov-wiki-compiler-caddy]=phase-b-business-architecture/org-units/kurpatov-wiki-compiler
  [kurpatov-wiki-ingest-caddy]=phase-b-business-architecture/org-units/kurpatov-wiki-ingest
  [rl-2048-caddy]=phase-b-business-architecture/org-units/rl-2048
)

active_caddies=()
for caddy in "${!LAB_OF_CADDY[@]}"; do
  if docker ps --format '{{.Names}}' | grep -qx "$caddy"; then
    active_caddies+=("$caddy")
  fi
done

if (( ${#active_caddies[@]} == 0 )); then
  cat >&2 <<EOF
== forge smoke: no lab is active ==

No lab caddy is running. Bring one up first, e.g.:
  make kurpatov-wiki-compiler
  make kurpatov-wiki-ingest
  make rl-2048

(Bench is a client of compiler — bring up compiler, then run bench
separately via make -C phase-b-business-architecture/org-units/kurpatov-wiki-bench bench.)
EOF
  exit 2
fi

if (( ${#active_caddies[@]} > 1 )); then
  cat >&2 <<EOF
== forge smoke: BROKEN MUTEX — multiple labs are up ==

Active caddy containers: ${active_caddies[*]}

Labs are supposed to be mutex on host :80/:443 — only one caddy
should bind. Investigate: a stale container may not have exited
cleanly. To fix: bring everything down first:

  make stop-all

then bring up the lab you actually want.
EOF
  exit 1
fi

active_caddy=${active_caddies[0]}
active_lab=${LAB_OF_CADDY[$active_caddy]}
lab_smoke="$ROOT_DIR/$active_lab/tests/smoke.sh"

if [[ ! -x "$lab_smoke" ]]; then
  echo "ERROR: $lab_smoke not found or not executable" >&2
  exit 2
fi

printf '== forge smoke: dispatching to %s ==\n' "$active_lab"
exec "$lab_smoke" "$@"
