# SOLUTION-ARCHITECTURE.md — reward-bench

Companion to [SPEC.md](SPEC.md) (lab contract) and
[CATS.md](CATS.md) (implementation discipline). One decision per
section. Current state only. Git holds the chronology.


## 1. What the bench is

```haskell
bench :: Env -> BenchConfig -> Submission
bench env cfg = argmaxBy (.score) (orchestrator env cfg)
```

A bench-run is the `argmax`-by-score over candidate `Submission`s
enumerated by an `orchestrator` strategy under a fixed `Env` and
`BenchConfig`. Everything else — context construction, sandbox
spawning, prompt shape — is a free parameter of `orchestrator`.

```python
Submission = (body: str, score: float, walltime_sec: float)
Env        = (tasks_dir: Path, canonical_scorer: Runner,
              model_client: ModelClient)
```


## 2. Three roles

Strict separation. The current ralph code fuses Orchestrator +
SolutionGenerator into one long-lived agent context; the target
architecture decomposes them.

```
Orchestrator        :: Env -> BenchConfig -> [Submission]
SolutionGenerator   :: ContextSnapshot -> SolverBody
Runner              :: SolverBody -> Seeds -> AttemptResult
```

```python
ContextSnapshot = {
    env_spec            : TaskSpec    # SPEC.md + env source + Solver contract
    best_so_far         : Submission  # running best body + its score
    history_digest      : [PriorIter] # prior bodies + scores, compressed
    iters_remaining     : int
    time_remaining_sec  : float
    budget_sec_per_seed : float
}
```

### Orchestrator

Owns cumulative state. Constructs a `ContextSnapshot` per iter
from that state. Hands the snapshot to the `SolutionGenerator`.
Hands the returned body to the `Runner`. Updates state from the
`AttemptResult`. Decides when to stop. Holds no model context.

The orchestrator's process is short and self-evident — it never
asks "what did I do five iters ago" because that lives in
`history_digest` as structured data.

### SolutionGenerator

Pure function from a fresh `ContextSnapshot` to a `SolverBody`
string. The LLM that writes code. Fresh context every iter — no
memory across iters except what the snapshot carries.
Deliberation tokens die with the iter.

The SolutionGenerator's context is bounded by the snapshot — 16K
tokens suffice when the snapshot is compact. Models with small
context windows compete fairly because the iter context is reset
each call.

### Runner

The canonical scorer. Body string in, `AttemptResult` out. No path
crosses this boundary (see §5). Already typed in code as:

```python
CanonicalScorerPort.score_body(body: str, seeds, *,
                               hard_wall_sec) -> AttemptResult
```


## 3. Fitness functions

Architectural shape (three checks gate role separation):

- `test_when_orchestrator_called_then_returns_iterable_of_submissions`
- `test_when_solution_generator_called_with_context_snapshot_then_returns_solver_body`
- `test_when_runner_score_body_called_then_returns_attempt_result`

Domain quality (one check gates output):

```
best_score env cfg t = max { score env s
                            | s in orchestrator env cfg,
                              s.walltime_sec <= t }
```

— for fixed `env` and walltime budget `t`, the highest-scoring
candidate submission.

Live end-to-end (one check gates the whole chain):

- `test_when_bench_called_with_real_ralph_chain_then_returns_submission_with_solver_body_and_non_negative_score`
  — produces a `Submission` whose `body` contains `class Solver`
  and `from transitions`, whose `score` is a non-negative float,
  whose `walltime_sec > 1.0`.


## 4. SolutionGenerator runtime: OpenHands

**OpenHands is the SolutionGenerator runtime.** Decision committed.

Each iter constructs an OpenHands task with:

- the `ContextSnapshot` rendered as the task prompt
- a tool surface bounded by what the SolutionGenerator needs
  (read env spec, write `submission.py`, request a `score_body`
  call from the Runner)
- the OpenHands agent context, freshly built per iter

The agent runs the task to completion (or its task-internal
budget), returns the final `submission.py` body as a string. The
orchestrator takes it from there.

OpenHands replaces:

- `src/tier1/agent_loop.py::run_loop` (the long-lived ralph loop)
- `Tool` / `ToolRegistry` / `ProtocolParser` ports (OpenHands has
  its own tool surface)
- The `execute_submission` dev-runner action

What stays ours (independent of OpenHands):

- `Submission`, `Env`, `BenchConfig`, `ContextSnapshot`,
  `AttemptResult` value types
- `CanonicalScorerPort.score_body` (the Runner Port)
- `MODEL_REGISTRY` and `BenchConfig` typed configuration
- Architecture fitness tests in `tests/architecture/`
- Leaderboard generation


## 5. No file APIs across module boundaries

Bench-side code communicates only in **strings, scalars, value
objects**. The only file IO sits inside
`DockerCanonicalScorer.score_body`'s private bind-mount tempfile —
invisible above the Runner.

This rules out `submission_path`, `workspace`, `env_dir`,
`tasks_dir` as parameters of any port or use case above the
Runner. The scorer constructs its own private tempfile, mounts it
into the container, scores, returns the `AttemptResult`. The path
never escapes the method.

The class of bug that path arithmetic produces — a wrong
`parents[N]` silently misrouting a Docker mount — is
unrepresentable when no module above the Runner computes paths.


## 6. Components

```
src/reward_bench/
    entities/      Submission, Env, BenchConfig, ModelTarget, ContextSnapshot
    use_cases/     bench, best_submission, best_score, dominates_at_budget
    adapters/      OrchestrateOpenHands (planned),
                   OrchestrateRalphSingleContext (legacy)
    frameworks/    main, bench_main (CLI entrypoints)

src/ports/         Orchestrator, CanonicalScorerPort, ModelClient
src/adapters/fakes/  Fake* for testing
src/tier1/         agent_loop (ralph, retiring),
                   DockerCanonicalScorer (the Runner adapter)
```

Per-module clean architecture: `entities` are pure value types,
`use_cases` are pure functions over ports, `adapters` cross
runtime boundaries, `frameworks` are CLI/wiring. Dependency
direction enforced by
[`tests/architecture/test_dependency_direction.py`](tests/architecture/test_dependency_direction.py).


## 7. Open items

- **`OrchestrateOpenHands` adapter** does not yet exist. The §3
  role-separation fitness tests gate it; building it is the next
  major implementation effort.
- **`bench_main.py` `REPO`/`TASKS_DIR` constants** still compute
  paths. §5 says no paths above the Runner; these constants are
  legacy and disappear with the OpenHands cutover.
- **`agent_loop._execute_submission` writes
  `workspace/submission.py`** for the snapshot pipeline (cycle 205
  reverted an attempt to drop it). The replacement is the §2
  SolutionGenerator returning the body in-memory; the workspace
  disappears with `agent_loop`'s retirement.
- **Bench bug — zero-score artifacts.** Some canonical Docker
  invocations return `score=0` despite a working submission. Under
  investigation; suspected in the canonical scorer path, not the
  model.
- **`MODEL_REGISTRY.max_model_len`** varies 16K–262K across
  registry entries. Today's ralph loop's accumulating history
  makes the smoke comparison context-window-biased. The §2
  SolutionGenerator with fresh per-iter context normalises this —
  all models compete inside the snapshot's bounded budget.
- **`MODEL_REGISTRY` duplication** between YAML and Python tuple.
  Load-from-YAML pending.
- **Condenser** trigger heuristic (4-chars-per-token estimate) is
  retired by §2: per-iter contexts don't accumulate, no condenser
  needed.
- **`validate_submission_protocol`** still calls
  `instance.move(test_board)` in the bench main thread — a wedge
  pattern. Wrap in `multiprocessing.Process` with hard timeout.
- **Static submission protocol** described in SPEC.md but not
  implemented; only the interactive tool-using SolutionGenerator
  loop currently exists.


## 8. Cross-references

- [SPEC.md](SPEC.md) — lab contract (Solver shape, scoring rules,
  task definition).
- [`forge/AGENTS.md`](../../../AGENTS.md) — repo-wide rules; this
  file inherits the Twain principle and Senior Haskell AI Engineer
  stance from there.
- [`tests/architecture/`](tests/architecture/) — fitness tests
  that enforce §§2-3, 5 invariants.

Forge phase reference: <https://www.opengroup.org/togaf>.
