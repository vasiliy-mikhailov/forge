# Smoke — wiki-ingest

Source of truth for [`./smoke.sh`](smoke.sh). Helpers come from
[`../../../../scripts/smoke-lib.sh`](../../../../scripts/smoke-lib.sh).

## Preconditions

- Lab is up: `make wiki-ingest`. Three pipeline containers
  (`jupyter-kurpatov-wiki`, `kurpatov-ingest`, `kurpatov-wiki-raw-pusher`)
  + the lab caddy.
- `forge/.env` has: `BASIC_AUTH_USER`, `MLFLOW_TRACKING_PASSWORD`
  (doubles as basic-auth plaintext by deployment convention),
  `JUPYTER_KURPATOV_WIKI_DOMAIN`, `KURPATOV_WIKI_GPU_UUID`.

## Section 1 — containers up

### container up: jupyter-kurpatov-wiki / kurpatov-ingest / kurpatov-wiki-raw-pusher / kurpatov-wiki-ingest-caddy

**Goal.** Every container of the ingest pipeline is running.

**Signals.** `docker ps` row matches name exactly, status starts with
`Up`. Healthcheck not asserted (none of these containers declare one
yet).

**Edge cases.**
- A container in a fast restart loop can appear "Up" briefly. Smoke
  doesn't retry; a real loop is obvious from a second run.

## Section 2 — GPU partitioning

### jupyter-kurpatov-wiki pinned to KURPATOV_WIKI_GPU_UUID

**Goal.** The jupyter container sees only the declared GPU. No
leakage from the rl-2048 GPU.

**Signals.** `docker exec jupyter-kurpatov-wiki nvidia-smi
--query-gpu=uuid --format=csv,noheader` (whitespace-stripped) equals
`$KURPATOV_WIKI_GPU_UUID`.

**Edge cases.**
- `kurpatov-ingest` deliberately shares the same GPU (whisper batch
  inference). We assert jupyter's view — duplicate assertion on
  ingest would be noise.
- `kurpatov-wiki-raw-pusher` is CPU-only and has no GPU device. It
  must NOT be in this assertion's container list.

## Section 3 — torch.cuda matmul

### torch.cuda matmul inside jupyter-kurpatov-wiki

**Goal.** GPU is not just visible but actually usable for compute.
Catches "GPU visible but driver/UVM unhappy" — the failure mode
[ADR 0004](../../../../phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md)
exists to prevent.

**Signals.** `docker exec jupyter-kurpatov-wiki python -c <snippet>`
exits 0 where the snippet runs `torch.cuda.is_available()`, allocates
two 1024×1024 tensors on CUDA, matmuls them, and `torch.cuda.synchronize()`s.

**Edge cases.**
- Use 1024×1024, not bigger. Big tensors can OOM under a warm jupyter
  kernel and turn a working stack into a false-fail.

## Section 4 — caddy basic auth

### jupyter-kurpatov-wiki via caddy

**Goal.** `$JUPYTER_KURPATOV_WIKI_DOMAIN` is fronted by caddy with
basic auth. Unauthenticated → 401, authenticated → reaches jupyter
backend.

**Signals.**
- `curl https://$JUPYTER_KURPATOV_WIKI_DOMAIN/` → 401.
- Same with `-u "$USER:$PASS"` → 200 or 302 (jupyter redirects `/`
  to `/lab` depending on session state).

**Edge cases.**
- Plaintext password is `MLFLOW_TRACKING_PASSWORD` by deployment
  convention — same secret doubles as caddy basicauth plaintext.
- Caddy ACME auto-renew can stall a single request several seconds;
  `--max-time 8` is the empirical knee.
- Never log the full `-u` line — keep the password out of `set -x`.

## Section 5 — reactive watchers

### ingest daemon has inotify on /workspace/sources

**Goal.** `kurpatov-ingest` actually entered its watchdog loop. A
container that booted but errored before `observer.schedule()` is
silently broken — `docker ps` still shows "Up".

**Signals.** `docker logs --since=24h kurpatov-ingest` contains
`inotify on /workspace/sources` at least once.

**Edge cases.**
- **Capture-then-grep discipline.** `docker logs ... | grep -q` under
  `set -o pipefail` SIGPIPE-fails when the log is large (grep closes
  stdin on first match, docker logs gets EPIPE). The shared helper
  `check_logs_contains` does `logs=$(docker logs ...)` then `grep -qE
  <<<"$logs"`. Don't bypass.
- The log phrase is part of the smoke contract. Any edit to the line
  in the daemon source needs a paired update here.

### raw-pusher has inotify on /workspace/vault/raw/data

Same shape, for `kurpatov-wiki-raw-pusher` and pattern
`inotify on /workspace/vault/raw/data` (the pusher watches the
content subtree under the data/content split — see ADR 0005 in this
lab's `docs/adr/`).

## Section 6 — pusher image discipline

### raw-pusher uses a dedicated lean image

**Goal.** `kurpatov-wiki-raw-pusher` only needs git + openssh-client
+ watchdog. Riding the ~20 GB GPU image bloats restart logs (NVIDIA
CUDA banner) and surface; see [`docs/adr/0006-lean-pusher-image.md`](../docs/adr/0006-lean-pusher-image.md)
in this lab.

**Signals.**
1. `docker inspect <pusher>` Image differs from `docker inspect
   <jupyter>` Image.
2. Pusher image size < 500 MB.

**Edge cases.**
- python:3.12-slim + git + openssh-client + watchdog is ~200 MB; the
  500 MB threshold is generous headroom while still catching an
  accidental `FROM forge-kurpatov-wiki:latest` regression.

## Section 7 — ingest startup reclaim

### ingest daemon ran [reclaim] startup pass

**Goal.** `kurpatov-ingest` ran its reverse-scan reclaim pass at the
last boot — the two-way sync code path (forward scan of sources,
reverse scan of raws, stale `*.tmp` sweep). See [`docs/adr/0008-ingest-dispatch.md`](../docs/adr/0008-ingest-dispatch.md)
in this lab.

**Signals.** `docker logs --since=24h kurpatov-ingest` contains
`[reclaim] startup pass complete`. The daemon emits this line on
every boot regardless of how many items were reclaimed, precisely so
this check has a stable heartbeat.

**Edge cases.** Same capture-then-grep discipline as Section 5.

## Known gaps

- "GitHub push actually worked." The pusher logs `[git  ] pushed` on
  success; not asserted today.
- `vault/raw/.git`'s remote URL = `kurpatov-wiki-raw`; not asserted today.
- `proxy-net` membership of each container; not asserted today
  (caught indirectly by HTTP checks).


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain (OKRs) inherited from the lab's AGENTS.md.
