# reward-bench — agentic comprehensiveness benchmark

## Purpose

BEAM-sandboxed evaluator. Runs a candidate LLM through a 4-tier
ladder of agentic puzzle-solving tasks; each tier asks the model to
produce an FSM (or FSM-of-agents) maximising a verifiable quantitative
reward. First task: 2048. Harness is task-agnostic.

reward-bench is **the comprehensiveness scoreboard** for forge.
Throughput is measured separately. reward-bench answers: "given a
model that is fast enough, can it actually orchestrate to solve a
task?"

Per [ADR 0029](../../../phase-preliminary/adr/0029-reward-bench.md).
Per [ADR 0015](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md),
scores are verifiable — derived from the env's deterministic reward
function, not from any judge.

## Non-goals

- Not a training lab. Training is `rl-2048`'s job. reward-bench is
  CPU-only evaluation.
- Not a UI. Headless. `bench_main:run/0` (or `make` target) runs one
  attempt and exits.
- Not coupled to one task. The harness is task-agnostic; today only
  2048 is wired in.
- Not a model server. We consume a vLLM endpoint from
  `${VLLM_BASE_URL}`; provisioning that is some other lab's job.

## Architecture

See [SOLUTION-ARCHITECTURE.md](SOLUTION-ARCHITECTURE.md) for the
three-role decomposition (Orchestrator / SolutionGenerator /
canonical_scorer) and the two-layer sandbox (outer docker for the
bench release, inner BEAM processes for Solver execution).

## Mode mutex

CPU-only. Co-runs with whichever lab is providing inference —
`${VLLM_BASE_URL}` must be reachable. The bench owns no inference
infrastructure.

## Required environment

- `VLLM_BASE_URL` — chat-completions endpoint root, e.g.
  `https://inference.mikhailov.tech` (or `/v1` suffix; the client
  normalises).
- `VLLM_API_KEY` — bearer token for the endpoint.
- `VLLM_MODEL_ID` — id the endpoint advertises for the candidate
  model.
- `MAX_ITERS` — orchestrator iterations per attempt (default 1).
- `HARD_WALL_SEC` — per-game Solver-execution wallclock cap, in
  seconds (default 60). The canonical scorer kills any game whose
  Solver runs past this. **NOT** a budget for LLM generation,
  compilation, observation, or orchestration — those run as long
  as they need, bounded only by `MAX_ITERS`.
- `SKILL_PATH` — path to the SKILL spec for the task (default
  `tasks/2048/SKILL_tier1.md`).

## Submission protocol

One protocol, no tools. The LLM receives an `env_spec` (task SKILL +
output rule + budget) and emits the candidate Solver as a fenced
```` ```erlang ... ``` ```` block in its assistant message. The
harness:

1. Extracts the last fenced erlang block as a binary.
2. Compiles via `compile:forms/2`, loads via `code:load_binary/3`.
3. Runs N canonical games in monitored Erlang processes, one process
   per seed.
4. Feeds aggregate scores back to the LLM as the next user message;
   the LLM iterates until it is satisfied or `MAX_ITERS` is reached.
5. Final body = the highest-scoring fenced block across iters.

No tool-call JSON. No file IO. No docker per Solver.

## Tier specifications

### Tier 1 — static Erlang FSM

- **Submission**: Erlang module named `submission` exporting
  `move/1`. The function takes a 4×4 board (list of 4 lists of 4
  non-negative integers; 0 = empty, tiles are powers of 2) and
  returns one of the atoms `w` | `a` | `s` | `d`.
- **Allowed surface**: any module:function/arity from the Erlang/OTP
  standard library, callable inside a pure `move/1`. No `spawn`,
  no `process_flag`, no `file:`, no `gen_tcp:` — the harness runs
  the Solver inside a sandboxed Erlang process; IO patterns the
  harness does not whitelist will fault the game.
- **Reward**: mean game score over 20 games on canonical held-out
  seeds 1000-1019.
- **Replay tolerance**: 0 % — the env is pure functional + seeded,
  so two runs of the same Solver against the same seeds must produce
  identical scores.
- **Author context**: solution_generator's reasoning loop, bounded
  by `MAX_ITERS` inner iterations. Each iteration is one LLM call
  plus one dev test against dev seeds; the observation message to
  the agent reports per-seed scores. The agent stops when it is
  satisfied or `MAX_ITERS` is reached — there is no wallclock cap
  on its reasoning.

### Tier 2-4

**Deferred.** Tiers 2-4 would generalise to open-world FSM-of-agents,
LangGraph-style orchestrations, meta-orchestrators that build the
solver dynamically. None of this is on the current roadmap. The
3-role architecture leaves room for it if/when tier-1 saturates.

## Make targets

See the [`Makefile`](Makefile) for the actual list. Summary:

```
make compile     rebar3 compile inside reward-bench-dev:0.1
make eunit       run EUnit suites
make ct          run Common Test suites
make shell       interactive rebar3 shell with deps loaded
make dialyzer    static type analysis
make release     build the deployment release
```

## Per-game wallclock + iteration caps

Each canonical game runs in its own monitored Erlang process. Two
caps guard runaway Solvers:

- **Wallclock**: each game has a hard deadline (`HARD_WALL_SEC`,
  flowed through from `bench_config`); on expiry the process is
  killed and the game's state is recorded as `wall_clock_expired`.
- **Move count**: capped at `?GAME_MOVE_CAP` (10000) in
  `beam_canonical_scorer`; on expiry the game ends as
  `max_moves_reached`.

A stagnation detector (no score / max-tile progress for N seconds)
is in scope for a later cycle.

## Cross-references

- [ADR 0029 — reward-bench](../../../phase-preliminary/adr/0029-reward-bench.md)
  — design decisions.
- [ADR 0015 — verifiable agent rewards](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
  — the first principle this lab realises.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: ADR 0029 — forge needs a verifiable comprehensiveness
  scoreboard.
- **Goal**: [Quality](../../../phase-a-architecture-vision/goals.md)
  (KR: `pre_prod_share ≥ 0.95`).
- **Outcome**: this lab + 4-tier ladder; first task 2048; leaderboard
  across registry models.
- **Measurement source**: lab-tests: RB (reward-bench EUnit + live
  smoke against real vLLM).
- **Contribution**: closes the throughput-only gap in model selection
  signal — comprehensiveness becomes diff-able.
- **Capability realised**: [Architecture knowledge management](../../../phase-b-business-architecture/capabilities/forge-level.md).
- **Function**: Provide-verifiable-comprehensiveness-signal-for-LLM-selection.
- **Element**: this directory.
