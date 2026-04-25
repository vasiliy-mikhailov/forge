# Smoke — kurpatov-wiki-bench

Source of truth for [`./smoke.sh`](smoke.sh). Helpers come from
[`../../../scripts/smoke-lib.sh`](../../../scripts/smoke-lib.sh).

Bench is a one-shot agent harness, not a long-running service — it has
no caddy, no compose, no port binding. This smoke is therefore
**static / pre-flight**: it verifies the bench can be *invoked*, not
that it *is invoked*.

Bench depends on the compiler lab being up (it talks to vLLM behind
caddy). It is co-runnable with the compiler lab. Top-level dispatcher
does NOT route to bench — bench's smoke is invoked explicitly via
`make -C labs/kurpatov-wiki-bench smoke`.

## Preconditions

- `forge/.env` has `OPENHANDS_VERSION`, `INFERENCE_BASE_URL`,
  `VLLM_API_KEY`, `INFERENCE_SERVED_NAME`.
- (Strongly recommended for section 4) compiler lab is up.

## Section 1 — OpenHands binary present

### bin/openhands exists and is executable

**Goal.** The OpenHands SDK CLI binary is present at
`labs/kurpatov-wiki-bench/bin/openhands`. The Dockerfile `COPY`s it
into the bench image during `make build`; if it's missing, the build
fails silently or the image runs without the agent.

**Signals.** `[[ -x .../bin/openhands ]]` is true.

**Edge cases.**
- If the binary was built locally on macOS while the bench image is
  Linux, `-x` succeeds but `docker run` fails at exec time. Smoke
  doesn't catch this — a real first-run validates it.

## Section 2 — bench docker image built

### image kurpatov-wiki-bench:$OPENHANDS_VERSION exists

**Goal.** `make build` finished and the image is in the local docker
image cache. Otherwise `bench/run.sh` fails preflight.

**Signals.** `docker image inspect kurpatov-wiki-bench:$OPENHANDS_VERSION`
exits 0.

**Edge cases.**
- If the user bumped `OPENHANDS_VERSION` in `.env` without running
  `make build`, this fails — desired behavior, the run would have
  failed anyway.

## Section 3 — GitHub auth

### gh auth token works

**Goal.** `gh auth token` returns a valid token; this token is what
bench/run.sh injects into the sandboxed container so the agent can
push to `kurpatov-wiki-{wiki,raw}` over HTTPS.

**Signals.**
- `gh` CLI installed.
- `gh auth token` exits 0 (some token returned).

**Edge cases.**
- Smoke doesn't validate that the token still has push permissions.
  A revoked token returns a value but the push fails inside the
  sandbox; that's a runtime error, surfaced in `events.jsonl`.

## Section 4 — compiler endpoint reachable + correct model

### compiler serves $INFERENCE_SERVED_NAME

**Goal.** Bench expects the compiler lab to be serving exactly the
model named in `.env`. Drift (e.g. compiler swapped to a different
model without updating .env) produces silent benchmark mismatches.

**Signals.**
- `GET ${INFERENCE_BASE_URL}/models` returns 2xx.
- The first `data[].id` equals `$INFERENCE_SERVED_NAME`.

**Edge cases.**
- If the compiler lab isn't up, this section fails — but a smoke
  fail here is not a bench bug, it's a "you need to bring up
  compiler lab first" signal. Phrasing of the failure message makes
  that clear.

## Known gaps

- This smoke does NOT issue a chat completion. A real round-trip
  test would catch parser-side drift, but it's expensive enough to
  warrant being a separate bench command (see
  `make -C labs/kurpatov-wiki-bench preflight` for an existing
  cheaper version of this).
- No assertion that `${STORAGE_ROOT}/labs/kurpatov-wiki-bench/experiments/`
  exists with write permissions. `make storage-init` is supposed to
  create it; smoke could verify.
