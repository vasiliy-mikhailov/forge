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
              model_client: ModelClient, env_spec: str)
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
    env_spec            : str         # self-contained prompt — see §4
    best_so_far         : Submission  # running best body + its score
    history_digest      : [PriorIter] # prior bodies + scores
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

- `test_when_bench_called_with_real_chain_then_returns_submission_with_solver_body_and_non_negative_score`
  — produces a `Submission` whose `body` contains `class Solver`
  and `from transitions`, whose `score` is a non-negative float,
  whose `walltime_sec > 1.0`.


## 4. SolutionGenerator runtime: OpenHands in docker

**OpenHands is the SolutionGenerator runtime, and it runs inside
an ephemeral docker container per `generate()` call.** Decision
committed.

### Binding interface

`env_spec` is a **self-contained prompt** built once at startup by
the env_factory. Three sections:

1. **Task** — the SKILL contract (FSM Solver class, `move(board)
   -> str` returning W/A/S/D).
2. **Dev test harness** — an inline shell command the agent runs
   via its bash tool to measure a candidate solver against dev
   seeds. The command is executable as-is — every host path is
   already baked in. OpenHands captures its stdout; the agent
   reads game scores from there.
3. **Budget** — wallclock seconds and iteration count.

The agent reads the prompt, iterates in its own scratch (bash
tool + dev harness via docker-in-docker, observing stdout), then
emits the final Solver code as a fenced ```` ```python ... ``` ````
block in its last assistant message. That fenced block IS the
submission.

### Time budget — binding requirement

`snapshot.time_remaining_sec` is a **contract**, not advisory:
the runtime MUST be killed at this deadline. The orchestrator
passes `cfg.hard_wall_sec` here per iter; the SolutionGenerator
adapter passes it to its runner; the runner wraps the container
spawn in `timeout N docker run ...`. When the kernel SIGTERMs the
container at the deadline, the host reads whatever stdout the
agent flushed before then — partial answer or empty.

This rules out cooperative deadlines (`threading.Timer`,
`Conversation.pause()`) which won't take effect until the next
LLM call boundary — too much slack inside a small budget.

### What does NOT cross the boundary

- **No `submission.py` file** between runner and agent. The body
  lives in the final assistant message, period.
- **No mounted task directory.** The agent reads `env_spec`; the
  dev harness command already contains every host path it needs.
- **No structured callback** from OpenHands back to the Runner.
  The agent uses its own bash tool to invoke docker; the canonical
  Runner runs separately later.

### Process model

```
host (bench_main)
  → subprocess.run([timeout, N, docker, run, --rm, -i, --network=host,
                   -v /var/run/docker.sock:/var/run/docker.sock,
                   -e OPENAI_API_KEY=..., ...
                   reward-bench-openhands-runner:0.1],
                   input=prompt, capture_output=True)
                                ↓
                       container starts (tini → python entrypoint.py)
                                ↓
                       reads prompt from stdin
                                ↓
                       OpenHands Conversation runs
                          - LLM calls go to vLLM via --network=host
                          - agent's bash tool runs `docker run reward-bench-tier1:0.4 ...`
                            using the mounted docker.sock
                                ↓
                       prints last agent message text to stdout
                                ↓
                  (host) extract_fenced_python(stdout) → body
```

The container's `/workspace` is ephemeral; nothing crosses to the
host filesystem from the agent's scratch. Wallclock is enforced
by the host's `timeout` wrapper, not by any in-SDK mechanism.

### Reference shape

```python
class OpenHandsSolutionGenerator:
    def generate(self, snapshot: ContextSnapshot) -> str:
        prompt = render(snapshot)             # task + harness + budget
        deadline = snapshot.time_remaining_sec or DEFAULT_DEADLINE_SEC
        return self._runner(prompt, deadline)

def make_default_openhands_runner(model_client, image=DEFAULT_IMAGE):
    def _runner(prompt: str, deadline_sec: float) -> str:
        proc = subprocess.run(
            ['timeout', str(int(deadline_sec)),
             'docker', 'run', '--rm', '-i',
             '--network=host',
             '-v', '/var/run/docker.sock:/var/run/docker.sock',
             '-e', f'OPENAI_API_KEY={model_client.api_key}',
             '-e', f'OPENAI_BASE_URL={model_client.base_url}',
             '-e', f'OPENAI_MODEL_ID={model_client.model_id}',
             image],
            input=prompt.encode(), capture_output=True, check=False,
        )
        return extract_fenced_python(proc.stdout.decode(errors='replace'))
    return _runner
```

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
invisible above the Runner. The OpenHands binding obeys the same
rule (§4): no `submission.py` flows between runner factory and
agent.

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
    adapters/      OrchestrateSubagentPerIter (default),
                   OpenHandsSolutionGenerator,
                   OrchestrateRalphSingleContext (legacy)
    frameworks/    main, bench_main (CLI entrypoints)

src/ports/         Orchestrator, SolutionGenerator,
                   CanonicalScorerPort, ModelClient
src/adapters/fakes/  Fake* for testing
src/tier1/         DockerCanonicalScorer (the Runner adapter);
                   agent_loop (legacy, retiring)
```

Per-module clean architecture: `entities` are pure value types,
`use_cases` are pure functions over ports, `adapters` cross
runtime boundaries, `frameworks` are CLI/wiring. Dependency
direction enforced by
[`tests/architecture/test_dependency_direction.py`](tests/architecture/test_dependency_direction.py).


## 7. Open items

- **`bench_main.py` `REPO`/`TASKS_DIR` constants** still compute
  paths to load env_spec at startup. The dev harness command
  inside env_spec also embeds absolute host paths. Acceptable for
  single-task tier-1; revisits when task selection lands.
- **`agent_loop`** still in tree, used by the legacy ralph
  orchestrator. Retires when OrchestrateRalphSingleContext is
  deleted.
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
