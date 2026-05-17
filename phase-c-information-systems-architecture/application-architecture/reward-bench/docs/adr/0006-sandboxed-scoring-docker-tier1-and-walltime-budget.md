# ADR 0006 — Sandboxed scoring: Docker tier-1 container + walltime budget enforcement

## Status

Accepted (2026-05-13). Active.

## Context

A campaign hung **34 minutes** at 95 % CPU, GPU idle. Root cause:
`score_submission` runs the model-generated Solver **in-process** with
no isolation, no walltime budget. The Solver implemented
expected-value lookahead × empty-cells per move — slow, and 20 × 3
trials blew past any reasonable cap.

Existing infrastructure on disk but unwired:

- `reward-bench/Dockerfile.tier1` — `reward-bench-tier1:0.3` already
  built locally. Pins numpy/transitions/pydantic; non-root; CMD runs
  `runner_canonical.py` on `/workspace/submission.py`.
- `tasks/2048/runner_canonical.py` — honours env:
  - `REWARD_BENCH_STAGNATION_SEC` default **60** — per-game stagnation
    detector; game ends `final_state='stagnated'` if neither `score`
    nor `max_tile` advanced.
  - `REWARD_BENCH_HARD_WALL_SEC` default **0** — outer runaway cap.
- SPEC.md mandates `docker run --network=none --rm
  reward-bench-tier1:VERSION ...` per attempt, with `/workspace` (rw),
  `/env` (ro), `/reports` (rw). Tier-1 offline; tiers 2-4 add
  `--network proxy-net` with iptables-restricted egress to
  `${INFERENCE_DOMAIN}`.

Current code: `score_submission` calls a `GameBoard2048Adapter` in the
orchestrator process — no isolation, no timeout. `AttemptResult` has
`stagnation_sec`, `hard_wall_sec`, `stagnated_any`, `walltime_exceeded`
fields, but they're hardcoded inert.

## Decision

Two-layer fix:

### 1. Application-layer aggregate cap

`score_submission` accepts `hard_wall_sec`. When > 0, between games the
use case checks `time.monotonic() - start > hard_wall_sec`; remaining
seeds become sentinel `GameResult(final_state='walltime_exceeded')`.

Minimum viable cap. Does NOT preempt a single hanging game — kicks in
between games.

### 2. Docker tier-1 sandbox

Replace `GameBoard2048Adapter` with a `DockerCanonicalScorer`:

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
   via `BenchConfig` plumbing (ADR 0015 sets canonical default 300 s).
4. Reads `/reports/result.json` + `events.jsonl`; maps to entities.

### Host-side: `--cpus=N` is the only knob

Parent picks `N = cpu_count() // 2` by default. `cpu_count()` comes via
a `CpuCountPort` DI seam (use-cases must not import `os`).

Tests inject `FakeCpuCount(8)` -> `--cpus=4`; production binds
`MultiprocessingCpuCount` -> typically 24 cores -> `--cpus=12`.

### Container-side: parallelise across cgroup-visible cores

`runner_canonical.py` uses `multiprocessing.Pool(processes=cpu_count())`.
`multiprocessing.cpu_count()` reads the cgroup CPU quota; the container
uses exactly the slice Docker gave it. No `max_workers` parameter
threads through the codebase.

### `hard_wall_sec` is enforced by Docker, not Python

Realised by `docker stop --time=N` (SIGTERM then SIGKILL), not a
daemon-thread `Thread.join(timeout=...)`. A Solver hung in a tight
Python loop is killed at the OS level. The in-container stagnation
detector (~60 s) remains primary for the common case.

Properties unlocked:

- **Per-game stagnation detector** kills hung games (preemption inside
  a game; aggregate cap is only between games).
- **Network isolation** (`--network=none`) enforces anti-exfil.
- **Image digest pinning** in `meta.json` — reproducibility.
- **Replay-determinism** — second run, scores match within tier tolerance.
- **Crash isolation** — segfault/OOM/hang doesn't take down the orchestrator.

## Consequences

### Positive (layer 1)

- **Bench survives slow Solvers.** Hang becomes a capped trial.
- **Cheap.** Pure Python; no Docker required.
- **Live signals.** `hard_wall_sec`, `walltime_exceeded` now used.

### Negative (layer 1)

- **No per-game preemption.** A single game hangs `hard_wall_sec + 1`
  before the cap fires.
- **In-process scoring.** Buggy Solver can leak, hold GIL, crash.

### Positive (layer 2)

- All SPEC.md guarantees met (stagnation, network policy, replay
  determinism, image-digest provenance, crash isolation).

### Negative (layer 2)

- Significant work: new adapter, env-var plumbing, JSON marshalling,
  Docker daemon dependency.
- Test-spec design fiddly (mocking docker, or running real containers).

## Alternatives considered

### A. Per-game cooperative timeout via `signal.alarm()`

**Rejected**: Unix-only; runs in main/pytest thread; interrupting user
code mid-stream leaves inconsistent state.

### B. Threading: daemon thread with join timeout

**Rejected**: Python threads can't be force-killed; abandoned threads
keep consuming CPU/memory.

### C. Multiprocessing: each game in `subprocess.Popen`

**Partially accepted** as a midpoint: `MultiprocessScoreAdapter` could
stepping-stone between in-process and Docker.

### D. Stay in-process

**Rejected**: T=0.7 makes the model write anything, including heavy
lookahead — the originating hang proves this fails.

## Implementation pointers

### Layer 1 — in-process scoring (narrowed scope)

`src/tier1/use_cases/score_submission.py` honours `hard_wall_sec` via a
between-game check; per-game daemon thread polls a deadline.

**Limitation**: daemon-thread soft timeout cannot interrupt C-level
work (busy loops, deepcopy, NumPy). The daemon worker eats a core, GIL
starves the main thread, the bench wedges.

Layer 1 is **still useful** for hermetic testing of the scoring
algorithm but is **no longer the production path**. Lives behind
`InProcessCanonicalScorer` (`src/adapters/in_process_canonical_scorer.py`),
implementing `CanonicalScorerPort` (ADR 0018).

### Layer 2 — Docker scoring (production for ALL runners)

`src/tier1/adapters/docker_canonical_scorer.py` — `DockerCanonicalScorer`
(ADR 0018). Spawns `reward-bench-tier1:${VERSION}` per attempt with
`--cpus=N` (`port.cpu_count() / 2`), `--memory=2g`, `--pids-limit=256`,
`--network=none`. Hard kill via cgroup.

**The dev runner ALSO uses Layer 2.** `_execute_submission` calls
`DockerCanonicalScorer.score()` with `dev_seeds=(1,2,3,4,5)` and
`hard_wall_sec=dev_hard_wall_sec`. Inherits hard kill plus multi-core
parallelism (~10× faster than in-process sequential).

`CanonicalScorerPort` (ADR 0018) abstracts both layers. Production
uses `DockerCanonicalScorer`; tests use `InProcessCanonicalScorer`
(hermetic) or `FakeCanonicalScorer` (scripted).

### Open follow-ups

- `validate_submission_protocol` still calls `instance.move(test_board)`
  in the bench main thread — same wedge pattern. A future cycle will
  wrap the runtime check in `multiprocessing.Process` with hard timeout.
- Future tier-2/3/4 Ports (LangGraph runner, orchestrator runner) will
  follow the ADR 0018 pattern (Real Docker adapter + Fake).

## Cross-references

- SPEC.md §Architecture and §Container topology
- `tasks/2048/runner_canonical.py`
- Lab ADR 0001 — "use the resource you already have"
- Lab ADR 0002 — structured result for any failure mode
- Lab ADR 0018 — `CanonicalScorerPort`
