# forge — all work runs in containers (policy)

**Status:** Forge-wide invariant
**Date:** 2026-04-26 (codified after D8-pilot audit revealed drift)
**Scope:** every lab under `forge/phase-c-information-systems-architecture/application-architecture/`, every executable artifact

This policy belongs at forge-level: promote into `forge/AGENTS.md` (or
`forge/phase-g-implementation-governance/policies/containers.md` if a dedicated policies dir exists).

---

## The rule

Every executable artifact in forge MUST run inside a Docker container:

- orchestrators (`run-*.py`)
- evaluators (`bench_grade.py`)
- helper scripts (`embed_helpers.py`, `factcheck.py`, `get_known_claims.py`)
- retrieval indexes (`embeddings/*.sqlite`, `*.npz`)
- LLM client invocations (vLLM HTTP via curl/python)

**No host-Python runs in production.** No host-pip installs of new
dependencies. No "works on the dev machine because libblas was already
installed."

## Why

1. **Reproducibility.** Every bench run must be replayable from
   `(artifact, Dockerfile)`. Host-state contamination
   (libssl version, libblas presence, system PATH) breaks this.

2. **Isolation.** Forge runs adversarial / under-test code (LLM agents
   running shell commands, fact-check scripts hitting Wikipedia,
   embeddings models downloading 280 MB from HF Hub). Containers
   bound the blast radius.

3. **System package consistency.** Real-world stacks need libblas /
   libssl / glibc / fonts in specific versions. The Dockerfile
   declares them; the host doesn't have to.

4. **Bench contract.** `bench-as-battery` (`run-battery.sh`,
   ADR 0008) assumes every model can be benched in a clean docker
   `up` → `bench` → `down` cycle. Host-Python orchestrators violate this.

## What we drifted on (2026-04-26 audit)

D7-rev2 ran inside a wrapped Docker image
(per ADR 0049 — `LD_LIBRARY_PATH`-leak workaround for the PyInstaller
openhands binary).

D7-rev3 onwards we shifted to running orchestrators directly from the
Python venv at `forge/phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/synthetic-orchestrator/.venv/`.
Reasoning at the time: openhands-sdk Python imports were faster to
iterate than rebuilding the docker image on each change, and the
DelegateTool/TaskToolSet workflows were still being prototyped.

**This was a tactical convenience, not a strategic shift.** Every run
since (D7-rev3 partial, D7-rev4-v2 5/7, D8 pilot 7/7) ran on host
Python. They were valid as TDD iterations; they would NOT pass a
strict reproducibility audit.

## Concrete remediation plan

For `wiki-bench` (the lab where drift is most pronounced):

### Step 1 — bake current dependencies into the bench Dockerfile

Add to `forge/phase-c-information-systems-architecture/application-architecture/wiki-bench/Dockerfile`:

```dockerfile
# OpenHands SDK (replaces standalone CLI binary)
RUN pip install --no-cache-dir \
    "openhands-sdk==1.17.0" \
    "openhands-tools==1.18.1"

# Retrieval (D8 Steps 1-3)
RUN pip install --no-cache-dir \
    "sentence-transformers>=2.7" \
    "numpy>=1.24" \
    "pyyaml>=6.0"

# Optional: sqlite-vss (requires libblas3 system pkg)
# Uncomment if/when we choose vss over numpy:
# RUN apt-get update && apt-get install -y libblas3 \
#     && rm -rf /var/lib/apt/lists/*
# RUN pip install --no-cache-dir sqlite-vss

# Pre-download embedding model into image (avoids HF Hub on every run)
RUN python3 -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('intfloat/multilingual-e5-base')"
```

### Step 2 — install our scripts into the image

Either:
- Copy `tests/synthetic-orchestrator/embed_helpers.py`,
  `evals/grade/bench_grade.py`, `orchestrator/run-d8-pilot.py` into
  `/usr/local/bin/` (or a dedicated `/opt/forge/`) inside the image, OR
- Mount the lab directory at runtime via `docker run -v $(pwd):/lab`
  and `cd /lab` in the entrypoint.

The first option is more reproducible (frozen at image build); the
second is more iteration-friendly. **Production runs MUST use option
1.** Spike runs can use option 2 with explicit "this is a spike, not a
publishable result" annotation in the post-mortem.

### Step 3 — `make bench` is the only entrypoint

`forge/phase-c-information-systems-architecture/application-architecture/wiki-bench/Makefile` should expose a single target:

```makefile
bench:
	docker compose run --rm bench python3 /opt/forge/run-d8-pilot.py
```

No bypass for "just run the script directly." If iteration speed
matters, make `make bench-spike` for the venv mode and clearly
flag its outputs as non-canonical.

### Step 4 — re-bench D8 pilot inside the container

Re-run `run-d8-pilot.py` inside the freshly-built image. Compare wall
time, claim counts, REPEATED detection. Expectation: identical
content (same Qwen-27B-FP8 endpoint), maybe ±5 % wall delta from
container overhead.

This re-run is the **canonical** D8 pilot result that gets committed
to `experiment/D8-pilot-...`. The host-venv run from 2026-04-26
becomes the spike artifact, kept for diff reference.

## Failure modes the policy prevents

- **D7-rev3+ libblas drift.** sqlite-vss couldn't load on host because
  `libblas3` wasn't installed (no sudo). In a container, the
  Dockerfile guarantees it; we'd never have seen this issue.

- **`LD_LIBRARY_PATH` PyInstaller leak (ADR 0049).** Solved at the
  Dockerfile level via wrapper scripts. Out of container, the leak
  poisons every subprocess and burns ~10 minutes of agent attention
  per run.

- **HF Hub rate-limit on cold start.** Re-downloading
  `multilingual-e5-base` (280 MB) on every fresh venv. Image bake
  caches it once.

- **"Works on my machine" replayability gap.** Without container, a
  reviewer cannot reproduce a result in less than ~30 minutes of
  setup. With container, `docker compose up` and they're running.

## Exceptions

- **Spike testing** (figuring out an SDK API, prototyping a sub-agent
  prompt) is allowed in venv. Output of a spike must NOT land in
  `bench/<date>-...` or `experiment/<exp-id>-...` branches as-is —
  it must be re-run in container before committing.

- **Local IDE inspection** (running `bench_grade.py --json` against
  a checked-out branch from your laptop) is fine; no commit follows.

- **CI** runs container images already; no additional config needed.

## Audit checklist for new artifacts

When reviewing a forge PR that adds an executable artifact, the reviewer
asks:

1. Is this script invoked via `make bench` / `make smoke` / a Dockerfile
   `RUN` / a `docker compose` service?
2. Are its dependencies pinned in the lab's Dockerfile?
3. Does the Dockerfile build successfully on a clean Linux host?
4. Does the script's documented usage example mention `docker run` or
   `make`, never `python3 path/to/script.py` as the canonical
   invocation?
5. If the artifact downloads anything at runtime (HF Hub model,
   external dataset), is this baked into the image?

If any answer is "no", the PR doesn't merge until fixed or until a
post-mortem-tagged spike artifact is explicitly out of scope.

## See also

- `forge:ADR/0049-Dockerfile-LD_LIBRARY_PATH-leak` — Dockerfile wrappers
  for openhands-sdk binary
- `forge:ADR/0008-bench-as-battery` — `run-battery.sh` + per-model
  Docker compose
- `wiki-bench/AGENTS.md` "Forge-wide invariant" section —
  lab-level mirror of this policy
- `outputs/D8-pilot-results.md` — first run that prompted this audit
