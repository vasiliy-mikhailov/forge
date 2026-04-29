#!/bin/bash
# Run test_verify_source_integration.py inside the bench container,
# matching production K1's environment as closely as possible per ADR 0010.
#
# Workspace: a fresh /tmp/integration-test-workspace on host, bind-mounted
# at /workspace inside the container (same pattern as K1).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_ROOT="$(cd "$HERE/../../../../.." && pwd)"
ORCHESTRATOR_DIR="$FORGE_ROOT/phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator"

WORKSPACE=/tmp/integration-test-workspace
sudo rm -rf "$WORKSPACE" 2>/dev/null || true
rm -rf "$WORKSPACE" 2>/dev/null || true
mkdir -p "$WORKSPACE"

# Copy test file + run-d8-pilot.py into the workspace so the container
# sees them at predictable paths.
cp "$HERE/test_verify_source_integration.py" "$WORKSPACE/test.py"

docker run --rm \
  --entrypoint python3 \
  -e ORCH_DIR=/opt/forge \
  -e LC_ALL=C.UTF-8 \
  -e LANG=C.UTF-8 \
  -v "$WORKSPACE:/workspace" \
  -v "$ORCHESTRATOR_DIR/run-d8-pilot.py:/opt/forge/run-d8-pilot.py" \
  kurpatov-wiki-bench:1.17.0-d8-cal \
  -u /workspace/test.py
