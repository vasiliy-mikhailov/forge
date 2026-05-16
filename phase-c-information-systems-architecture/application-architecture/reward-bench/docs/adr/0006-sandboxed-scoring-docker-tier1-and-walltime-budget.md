# ADR 0006 — Sandboxed scoring: Docker tier-1 container + walltime budget enforcement

## Status

Accepted (2026-05-13). Active.

## Context

Cycle-22 campaign hung **34 minutes** at 95 % CPU, GPU idle. Root
cause: `score_submission` runs the model-generated Solver
**in-process** with no isolation and no walltime budget. The Solver
implemented expected-value lookahead × empty-cells per move — not
infinite-loop, just very slow, and 20 canonical games × 3 trials
blew far past any reasonable cap.

Existing `_bak` / SPEC.md infrastructure that we **already have on
disk but have not wired**:

- `reward-bench/Dockerfile.tier1` — image versions 0.1 → 0.2 → **0.3**
  already built locally as `reward-bench-tier1:0.3` (228 MB). Pins
  numpy, transitions, pydantic; runs as non-root; CMD invokes
  `runner_canonical.py` against `/workspace/submission.py`.
- `tasks/2048/runner_canonical.py` — runs INSIDE the container.
  Honours env vars:
  - `REWARD_BENCH_STAGNATION_SEC` default **60** — per-game
    stagnation detector. A game ends with `final_state='stagnated'`
    if neither `game.score` nor `game.max_tile` has increased for
    that many wall-seconds. Replaces the original "5-min hard cap"
    with a uniformly applied detector that works for any tier.
  - `REWARD_BENCH_HARD_WALL_SEC` default **0** (disabled) — optional
    outer runaway-protection cap across the whole 20-game eval.
- SPEC.md §Architecture mandates the sandbox: `docker run
  --network=none --rm reward-bench-tier1:VERSION ... runner_canonical.py`
  per attempt, with mounts `/workspace` (rw), `/env` (ro),
  `/reports` (rw). Tier-1 runs offline (no network); tiers 2-4 add
  `--network proxy-net` with iptables-restricted egress to
  `${INFERENCE_DOMAIN}` only.

Our re-implementation (cycles 1-22):

- `score_submission` (use case) takes a `GameEnvPort` adapter and
  iterates `seeds`, calling `env.play_one_game(solver, seed)` for
  each. The adapter `GameBoard2048Adapter` instantiates a
  `GameBoard` directly in the orchestrator process and plays the
  game synchronously. No isolation, no timeout.
- `AttemptResult` carries `stagnation_sec`, `hard_wall_sec`,
  `stagnated_any`, `walltime_exceeded` fields (cycles 1-8) but
  `score_submission` hardcodes them to defaults — the fields are
  inert.

## Decision

Two-layer fix:

### 1. Application-layer aggregate cap

`score_submission` accepts a `hard_wall_sec` parameter. When > 0,
between games the use case checks `time.monotonic() - start >
hard_wall_sec`; if exceeded, remaining seeds become sentinel
`GameResult(final_state='walltime_exceeded')` and the returned
`AttemptResult.walltime_exceeded` is `True`. The cap is honoured by
the use case alone — no adapter changes.

This is the **minimum viable cap**. It does NOT preempt a single
hanging game; the first slow game still runs to completion before
the cap kicks in. For the cycle-22 observed hang, a 60 s cap would
have terminated the campaign after the first game (~60 s) instead
of running for 34+ minutes.

### 2. Docker tier-1 sandbox

Replace `GameBoard2048Adapter` with a `DockerCanonicalScorer`
adapter (cycle 105):

1. Copies `submission.py` and the env to a workspace directory.
2. Invokes:

   ```
   docker run --rm --network=none \
     --memory=2g --pids-limit=256 \
     --cpus=${CANONICAL_CPUS} \          # cycle 105: host-side cap
     -v <workspace>:/workspace \
     -v <env>:/env:ro -v <reports>:/reports \
     -e REWARD_BENCH_NUM_GAMES=20 \
     -e REWARD_BENCH_SEED_BASE=1000 \
     -e REWARD_BENCH_HARD_WALL_SEC=${HARD_WALL_SEC} \
     reward-bench-tier1:${TAG}
   ```

3. Honours `REWARD_BENCH_STAGNATION_SEC` / `REWARD_BENCH_HARD_WALL_SEC`
   env vars via the `BenchConfig` plumbing (cycle 104 / ADR 0015 sets
   the canonical default to 300 s).
4. Reads `/reports/result.json` + `events.jsonl`; maps to entities.

### Host-side: `--cpus=N` is the only knob

The bench parent picks `N` as `cpu_count() // 2` by default (cycle 105;
50 % of host cores). `cpu_count()` is supplied via a `CpuCountPort`
DI seam so the `score_submission` use-case stays free of `os` imports
(architecture rule: use-cases must not import `os`).

Tests inject a fixed-count fake (`FakeCpuCount(8)` -> `--cpus=4`);
production binds `MultiprocessingCpuCount` -> reads
`multiprocessing.cpu_count()` -> typically 24 on the lab host ->
`--cpus=12`.

### Container-side: parallelise across cgroup-visible cores

Inside the container, `runner_canonical.py` parallelises the N-seed
canonical eval via `multiprocessing.Pool(processes=cpu_count())`.

`multiprocessing.cpu_count()` inside a Docker container reads the
cgroup CPU quota that `--cpus=N` imposes — so the container "sees"
exactly the slice Docker gave it and uses all of it.

Result: the host only thinks in `--cpus` numbers; the container
auto-parallelises across that quota; no `max_workers` parameter
threads through the codebase.

### `hard_wall_sec` is enforced by Docker, not Python

The parent's hard cap is realised by `docker stop --time=N` (clean
SIGTERM, then SIGKILL after the grace period) rather than the cycle
27 daemon-thread `Thread.join(timeout=...)` antipattern. A Solver
that hangs in a tight Python loop is killed at the OS level, not
abandoned in a zombie thread.

The cycle 78 / runner v0.3 in-container stagnation detector remains
the primary bound for the common case (~60 s of no `score / max_tile`
progress => `final_state="stagnated"`).

Properties this unlocks:

- **Per-game stagnation detector** kills hung games (the actual
  preemption we need; the application-layer cap can only kick in
  between games).
- **Network isolation** (`--network=none` for tier 1) enforces
  SPEC.md anti-exfil contract.
- **Image digest pinning** in `meta.json` — full reproducibility
  audit-trail per SPEC.md.
- **Replay-determinism** (Stage 3) — second container run on the
  same submission, scores must match (within tier replay tolerance
  per `TIER_REGISTRY`).
- **Crash isolation** — a Solver that segfaults / OOMs / hangs
  doesn't take down the bench orchestrator.

## Consequences

### Positive (layer 1)

- **Bench survives slow Solvers.** Cycle-22 hang becomes a 60-s
  capped trial with a sentinel row — campaign continues.
- **Cheap.** No Docker required to land this; pure Python change.
- **Existing entity fields used.** `hard_wall_sec` and
  `walltime_exceeded` become live signals.

### Negative (layer 1)

- **Per-game preemption missing.** A single game that hangs for
  `hard_wall_sec + 1 second` blocks the use case for the full game
  duration before the cap fires. SPEC.md's `STAGNATION_SEC`
  preempts INSIDE a game; the aggregate cap does not.
- **In-process scoring.** A buggy Solver can still leak memory,
  hold the GIL, or crash the orchestrator. The full
  `--network=none` isolation isn't there yet.

### Positive (layer 2)

- All SPEC.md guarantees met (stagnation, network policy, replay
  determinism, image-digest provenance, crash isolation).
- Closes the operational gap to `_bak`'s legacy bench design.

### Negative (layer 2)

- Significant work: new adapter, new framework code, env-var
  plumbing, JSON marshalling, Docker daemon dependency on the host.
- Test-spec strategy needs careful design (mocking docker is
  fiddly; the proper test runs the real container, slowish).

## Alternatives considered

### A. Per-game cooperative timeout via `signal.alarm()`

Use `signal.alarm()` to raise an exception inside the Solver after
`N` seconds. **Rejected** because (a) it's Unix-only, (b) it runs
in the main thread which is also pytest's, (c) interrupting
arbitrary user code mid-stream can leave inconsistent state. The
Docker sandbox solves the same problem properly.

### B. Threading: run each game in a daemon thread with a join timeout

Spawn each game in a thread; if it doesn't return in
`stagnation_sec`, abandon it. **Rejected** because Python threads
can't be force-killed; an abandoned thread keeps consuming CPU and
memory until the orchestrator exits.

### C. Multiprocessing: each game in a `subprocess.Popen`

Closer to Docker but no isolation. **Partially accepted** as a
midpoint: a `MultiprocessScoreAdapter` could be a stepping stone
between in-process and Docker. **Queued** as a possible cycle 24
if Docker integration proves too heavy.

### D. Stay in-process; rely on the model not writing slow code

The status quo. **Rejected** because cycle-22 just proved this
fails: T=0.7 makes the model write whatever it wants, including
heavy lookahead.

## Implementation pointers

### Layer 1

- `src/tier1/use_cases/score_submission.py` — accept
  `hard_wall_sec: float = 0.0` parameter; between-game check.
- `tests/tier1/use_cases/test_score_submission.py` — stub
  `GameEnvPort` that sleeps; assert sentinel-fill on cap.
- `src/reward_bench/frameworks/main.py` — pass
  `config.hard_wall_sec` through (requires adding the field to
  `BenchConfig` first or a separate parameter; minimal-change
  pass-through via an explicit kwarg works for the campaign tests).

### Layer 2

- `src/tier1/adapters/sandboxed_score.py` — Docker-invoking
  `GameEnvPort` impl.
- `src/tier1/frameworks/docker_driver.py` — the docker run
  wrapper (volume mounts, env-var passing, JSON read-back).
- `BenchConfig.stagnation_sec` and `BenchConfig.hard_wall_sec`
  fields (ADR 0003 amendment).
- ADR-0006 follow-up describing the sandbox-result entity
  marshalling.

## Cross-references

- SPEC.md §Architecture and §Container topology
- `tasks/2048/runner_canonical.py` (already in repo; not yet wired)
- Lab ADR 0001 (same-model condenser — analogous "use the resource
  you already have" pattern)
- Lab ADR 0002 (sentinel-on-malformed — same robustness philosophy:
  the bench produces a structured result for any failure mode)
- Task #6 — Real-system bug: campaign hung 34 min (originating
  observation)
- Task #7 — Wire SPEC.md Docker-sandbox (layer 2 cycle)
