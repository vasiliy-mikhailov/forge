# Smoke test model

Covers `make smoke` / `scripts/smoke.sh`. This is the source of truth
for what the smoke test asserts. See [`tests/README.md`](README.md) for
the TDD workflow and check conventions.

## Preconditions

The smoke test assumes:

- `.env` is present at the forge root. Required variables: `BASIC_AUTH_USER`,
  `MLFLOW_TRACKING_PASSWORD`, `MLFLOW_DOMAIN`, `JUPYTER_RL_2048_DOMAIN`,
  `JUPYTER_KURPATOV_WIKI_DOMAIN`, `RL_2048_GPU_UUID`, `KURPATOV_WIKI_GPU_UUID`.
- The host has booted, `docker` is running, GPU driver is the
  MIT/GPL `-open` variant with `uvm_disable_hmm=1` (per
  [`docs/adr/0004-nvidia-driver-open-plus-hmm-off.md`](../docs/adr/0004-nvidia-driver-open-plus-hmm-off.md)).
- All services have been brought up (`make base && make rl-2048 && make kurpatov-wiki`).

The smoke test is **read-only**. It must not start, stop, or mutate
any container; all failures are diagnostic, not destructive.

## Overall contract

**Goal.** `make smoke` exits 0 iff forge is in a state where a user
can reasonably expect every advertised feature to work. Exit non-zero
must mean "something is actually broken," not "the check was flaky."

**Signals.**
- Exit code is 0 on full success, 1 on any failed check, 2 on missing
  prerequisites (no `.env`, required env var unset).
- Output is a sequence of `[ OK ]` / `[FAIL]` lines grouped by
  section, plus a `== summary ==` tallying passed/total.
- A failing check prints enough detail to triage without additional
  commands (e.g. "got X want Y", not just "mismatch").

**Edge cases.**
- Must be idempotent: running it five times in a row must always
  produce the same output unless state actually changes. No stateful
  assertions (e.g. "log contains exactly one X").
- Must not leak secrets: `MLFLOW_TRACKING_PASSWORD` shows up in HTTP
  auth calls; it must never be echoed on success lines or in failure
  messages.
- Must not depend on the current working directory of the caller —
  the script resolves its own location and `cd`s there.

---

## Section 1 — containers up

### container up: caddy / mlflow / jupyter-rl-2048 / jupyter-kurpatov-wiki / kurpatov-transcriber / kurpatov-wiki-raw-pusher

**Goal.** Every forge service container is running. The expected set
is exactly 6 containers; adding or removing a service means updating
this check.

**Signals.**
- `docker ps --format '{{.Names}}\t{{.Status}}'` contains a line whose
  name column exactly matches the expected container name and whose
  status column starts with the word "Up".
- All six containers pass. Missing any one is a hard fail.

**Edge cases.**
- Exact name match, not prefix. A leftover `jupyter-kurpatov-wiki-old`
  from an aborted rename must not satisfy the `jupyter-kurpatov-wiki`
  check.
- Status starts with "Up", not equals "Up". `Up 3 hours` and
  `Up (healthy)` and `Up (unhealthy)` are all passing states for
  today's smoke — we don't yet declare healthchecks. When we do, the
  model gets stricter here.
- A container in a fast restart loop can appear "Up" briefly and
  "Restarting" in between. Running the smoke during a loop-low window
  races; acceptable for now because such a loop is obvious from
  `docker ps` on a second run.

---

## Section 2 — GPU partitioning

### rl-2048 pinned to RL_2048_GPU_UUID

**Goal.** `jupyter-rl-2048` sees exactly the GPU declared for it in
`.env`. Nothing leaks from the sibling kurpatov-wiki GPU.

**Signals.**
- `docker exec jupyter-rl-2048 nvidia-smi --query-gpu=uuid --format=csv,noheader`
  returns a single line equal to `$RL_2048_GPU_UUID` (whitespace
  stripped).

**Edge cases.**
- If `nvidia-smi` inside the container sees *multiple* GPUs, the
  current single-line comparison silently matches the first and hides
  leakage. Tightening: assert the output has exactly one non-empty
  line. Left as a known gap today because compose pins via
  `device_ids`, which is hard to misconfigure.
- UUIDs include whitespace / stray CR from the container's output on
  some driver versions. Always strip `[:space:]` on both sides before
  comparing.

### kurpatov-wiki pinned to KURPATOV_WIKI_GPU_UUID

Same goal / signals / edge cases as above, but for
`jupyter-kurpatov-wiki` and `$KURPATOV_WIKI_GPU_UUID`.

**Edge cases (additional).**
- `kurpatov-transcriber` and `jupyter-kurpatov-wiki` deliberately
  share one GPU (see
  [`kurpatov-wiki/docs/adr/0003`](../kurpatov-wiki/docs/adr/0003-watcher-reactive-not-cron.md)).
  The smoke checks jupyter's view, not the transcriber's, because
  they're identical by construction — duplicate assertion would be
  noise.
- `kurpatov-wiki-raw-pusher` is CPU-only and has no GPU device; it
  must be absent from any GPU assertion. An accidental GPU
  reservation on the pusher shows up as "GPU unavailable at startup"
  in its own logs (nvidia CUDA banner warning), not here.

---

## Section 3 — torch.cuda matmul

### torch.cuda matmul inside jupyter-rl-2048 / jupyter-kurpatov-wiki

**Goal.** Each GPU container can not only see the GPU but actually
run a trivial CUDA kernel. This catches "GPU visible but driver/UVM
unhappy" — the failure mode ADR 0004 exists to prevent.

**Signals.**
- `docker exec <container> python -c '<snippet>'` exits 0, where the
  snippet asserts `torch.cuda.is_available()`, allocates two 1024×1024
  tensors on CUDA, matmuls them, and calls `torch.cuda.synchronize()`.

**Edge cases.**
- The snippet's stdout/stderr are suppressed on success. On failure
  the user gets only "FAIL" — acceptable because a real failure here
  is always caught by bringing up the container manually and running
  the snippet yourself. Documenting this to set expectations.
- Must use 1024×1024, not something bigger. Big tensors can OOM under
  a warm jupyter kernel and turn a working stack into a false-fail.
- `torch.__version__` is printed on success but only to stdout which
  we discard. If a test author needs the version, read it from
  `docker exec <c> python -c 'import torch; print(torch.__version__)'`
  outside this check — not by loosening the current redirect.

---

## Section 4 — Caddy basic auth

### mlflow / jupyter-rl-2048 / jupyter-kurpatov-wiki via caddy

**Goal.** Each public hostname is fronted by caddy with basic auth.
Unauthenticated requests get `401`; authenticated requests reach the
backend and return its normal "I'm alive" response.

**Signals (per domain).**
- `curl -sSo /dev/null -w '%{http_code}' https://$DOMAIN/` returns
  `401`.
- `curl ... -u "$BASIC_AUTH_USER:$MLFLOW_TRACKING_PASSWORD"` returns:
  - `200` for mlflow (its landing page).
  - `200` or `302` for jupyter hosts (they redirect `/` to `/lab`
    depending on whether a prior session is present).

**Edge cases.**
- The plaintext password is `MLFLOW_TRACKING_PASSWORD` by convention
  in this deployment — it doubles as the caddy basicauth plaintext.
  If that convention changes, the model changes too; until then,
  don't introduce a second secret for the smoke test.
- `--max-time 8` on every curl. Caddy's ACME auto-renew can stall a
  single request for several seconds; 8 is empirically the knee where
  real failures dominate over renewal noise. Don't lower.
- Network unreachable (DNS, firewall) returns code `000` in our curl
  format. That falls through to FAIL with clear "got 000" text. Do
  not retry — the smoke must be fast and honest.
- Never log the full `-u "$USER:$PASS"` curl line. The script keeps
  the password out of `set -x` / echo paths.

---

## Section 5 — mlflow REST API

### mlflow /api/2.0/mlflow/experiments/search

**Goal.** mlflow is not just reachable but actually answering API
calls with valid JSON — the basic-auth layer alone passing is not
enough (caddy could be 200ing a stale cache or a misrouted backend).

**Signals.**
- `POST https://$MLFLOW_DOMAIN/api/2.0/mlflow/experiments/search` with
  body `{"max_results":1}` and basic auth returns a body containing
  the substring `"experiments"`.

**Edge cases.**
- Substring match is deliberately loose — we don't want the smoke to
  break when mlflow's JSON shape shifts minor details between
  versions. If mlflow ever changes the top-level key, update here
  and in the script in one commit.
- The script captures the response body and truncates it to 200 chars
  in the failure message. Do not raise this cap — a misrouted backend
  can return MB of HTML and flood the terminal.
- Must use POST with `-H 'Content-Type: application/json'` even for
  `experiments/search` — the API rejects form-encoded bodies.

---

## Section 6 — reactive watchers

### transcriber has inotify on /workspace/sources

**Goal.** `kurpatov-transcriber` has actually entered its watchdog
loop. A container that booted but errored before `observer.schedule()`
is silently broken — `docker ps` still shows "Up" because the Python
process hasn't exited yet.

**Signals.**
- `docker logs --since=24h kurpatov-transcriber 2>&1` contains the
  string `inotify on /workspace/sources` at least once.

**Edge cases.**
- **Large log + `grep -q` + `pipefail` = SIGPIPE false-fail.** If the
  check is written as
  `docker logs ... 2>&1 | grep -qE 'pattern'`
  inside a script with `set -o pipefail`, `grep -q` exits on first
  match, closes stdin, `docker logs` writes again, gets SIGPIPE
  (exit 141), and pipefail propagates — failing the check even
  though the match was found. Observed in the wild on 2026-04-19:
  the transcriber check passed by luck (small log, match near the
  end), the raw-pusher check failed reliably because its logs carry
  the multi-line NVIDIA CUDA banner after every restart. **Discipline:
  capture `docker logs` into a variable first, then `grep -qE`
  against a here-string.** No pipe, no SIGPIPE.
- 24h window is arbitrary but intentional: shorter would false-fail
  a long-running healthy container; much longer would wastefully
  scan a log we've already cared about.
- Phrase must be stable. Any change to the log line in
  `03_watch_and_transcribe.py` / `04_watch_raw_and_push.py` is a
  change to this check's signal and needs a matching model + script
  update.

### raw-pusher has inotify on /workspace/vault/raw/data

Same goal / signals / edge cases as above, but for
`kurpatov-wiki-raw-pusher` and the string
`inotify on /workspace/vault/raw/data`. The pusher watches the
content subtree (`--raw`, default `/workspace/vault/raw/data`), not
the git working tree root — see ADR 0005's data/content-split
amendment.

**Edge cases (additional).**
- The raw-pusher's logs include the NVIDIA CUDA banner on every
  container restart (it runs the forge-kurpatov-wiki image which has
  the CUDA base), despite the pusher not using the GPU. That banner
  padding is what historically triggered the SIGPIPE false-fail —
  keep the "capture first, then grep" discipline even if the logs
  ever look small again.
- The pusher's `initial sync` log line also fires regardless of
  whether there's anything to commit — it's a heartbeat, not a
  content signal. Don't key the check to `initial sync` or to the
  commit log line, because those are cadence-dependent and
  volume-dependent.

---

## Section 7 — pusher image discipline

### raw-pusher does not use the GPU image

**Goal.** `kurpatov-wiki-raw-pusher`'s job is `git add/commit/push` over
SSH. It has no business dragging a 20 GB CUDA stack. The pusher must
run a dedicated lean image — no torch, no whisper, no nvidia base.

**Signals.**
- `docker inspect kurpatov-wiki-raw-pusher --format '{{.Config.Image}}'`
  returns an image *different from* the one used by
  `jupyter-kurpatov-wiki` and `kurpatov-transcriber`. The shipped pair
  today is `forge-kurpatov-wiki:latest` (GPU) vs.
  `forge-kurpatov-wiki-pusher:latest` (lean).
- `docker image inspect <pusher-image> --format '{{.Size}}'` returns
  a size under 500 MB. A python-slim + git + openssh-client +
  watchdog image is ~200 MB; 500 MB gives generous headroom for the
  slim base bumping a major version or for a few extra apt packages,
  while still catching accidental `FROM forge-kurpatov-wiki:latest`
  regression.

**Edge cases.**
- Two images tagged identically would false-pass the "different from"
  check. Not a real risk under our naming scheme but worth noting.
- The 500 MB threshold is policy, not physics. If a future dependency
  legitimately pushes the pusher past 500 MB, update this model file
  first (raise the number, document why) rather than silently
  relaxing the script.
- The NVIDIA CUDA banner at the top of `docker logs
  kurpatov-wiki-raw-pusher` was the symptom that motivated this
  split — a daemon using 0% of the GPU still printed "GPU
  functionality will not be available" on every restart, polluting
  logs and indirectly causing the `grep -q` + `pipefail` SIGPIPE
  bug. The asserted signal is image identity/size, not log
  absence, because a log-absence check would silently pass if NVIDIA
  ever removed the banner from their base image.
- Whichever image is built first wins the local cache. Both images
  must be built in sync; `make kurpatov-wiki-build` runs
  `docker compose build` which builds every service that declares a
  `build:` block, so this is handled at the compose layer, not by
  the test.

---

## Known gaps

Things the smoke test does *not* currently verify, but should someday:

- **GitHub push actually worked.** The pusher logs `[git  ] pushed`
  on success and `[git  ] push failed: <err>` on failure; neither is
  asserted today. A false "pusher is alive" positive is possible if
  the deploy key has rotted. Adding the assertion requires deciding
  what window to look at (last commit, last hour, etc.).
- **Remote URL on vault/raw/.git matches `kurpatov-wiki-raw`.** A
  silently-wrong remote would make the pusher push to the wrong
  place. Cheap check, not yet added.
- **GPU UUIDs in `.env` match `nvidia-smi -L` on the host.** A stale
  `.env` after a GPU reseat would OOM the second service; the current
  per-container check passes in that case because each container just
  sees "its" GPU and doesn't notice they've collided.
- **proxy-net exists and has each service attached.** A container
  that lost its network attachment is caught indirectly by the HTTP
  checks, but the diagnostic is worse than it needs to be.

When these become worth the time, document the new check here first,
then add the assertion to `scripts/smoke.sh`.
