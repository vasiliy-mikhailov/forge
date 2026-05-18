# SOLUTION-ARCHITECTURE.md — reward-bench

Companion to [SPEC.md](SPEC.md) (lab contract) and
[CATS.md](CATS.md) (implementation discipline). One decision per
section. Current state only. Git holds the chronology.


## 1. What the bench is

```erlang
-spec bench(env(), bench_config()) -> submission().
bench(Env, Cfg) ->
    lists:foldl(
        fun(S, Best) when S#submission.score > Best#submission.score -> S;
           (_, Best) -> Best
        end,
        #submission{score = -1.0},
        orchestrator:run(Env, Cfg)).
```

A bench-run is the `argmax`-by-score over candidate `#submission{}`s
enumerated by an orchestrator strategy under a fixed Env and
BenchConfig. Everything else — context construction, sandbox
spawning, prompt shape — is the orchestrator's choice.

```erlang
-record(submission, {
    body         :: binary(),    %% Erlang module source
    score        :: float(),
    walltime_sec :: float()
}).

-record(env, {
    tasks_dir        :: file:filename(),
    canonical_scorer :: pid() | atom(),   %% gen_server | module behaviour callback
    model_client     :: pid(),
    env_spec         :: binary()          %% rendered prompt — see §4
}).
```

Bodies are **module source binaries**: the literal text of an
Erlang module that exports `move/1`. The canonical scorer compiles
this in-memory via `compile:forms/2` + `code:load_binary/3` — no
disk hop, no `erlc` invocation, no submission.erl file.


## 2. Three roles

Each is an Erlang process. Strict separation, message-passed.

```
                       bench(Env, Cfg)
                            │
                            ▼
                     orchestrator (gen_server, transient)
              ┌─────────────┴─────────────┐
   {generate, │                           │ {score_body,
    Snapshot} ▼                           ▼  Body,Seeds}
   solution_generator                canonical_scorer
       (gen_server)                    (behaviour;
              │                         in-VM impl)
       loops: prompt                         │
       → vLLM (hackney)                      │
       → extract body                        │
       → dev_test ┐                          │
              │   │                          │
              │   └─► canonical_scorer:─────►│
              │       score_body(B, DevSeeds)│
              ▼                              ▼
              body                  per-seed Erlang process:
                                    spawn_monitor(runner_canonical,
                                                  play_game,
                                                  [Submission, Seed, ...])
                                    │
                                    ▼
                                 #attempt_result{}
```

Solver code executes inside **Erlang processes** spawned by
`canonical_scorer`. One process per game seed; the process is
monitored, given a soft memory cap and a wallclock deadline. See
§5. No external sandbox, no docker.

`dev_test` and `canonical_scorer:score_body` are the same call
with different seed ranges — `dev_test` is just a convenience
wrapper that passes `dev_seeds()` from `compose_env_spec`.

### Records

```erlang
-record(context_snapshot, {
    env_spec            :: binary(),
    best_so_far         :: #submission{},
    history_digest      :: [#submission{}],
    iters_remaining     :: non_neg_integer(),
    time_remaining_sec  :: float(),
    budget_sec_per_seed :: float()
}).
```

### Orchestrator

```erlang
-module(orchestrator).
-behaviour(gen_server).
-export([run/2]).
-spec run(env(), bench_config()) -> [submission()].
```

Started transiently per `bench/2` call. Holds cumulative state
(running best, history). Per iter:

1. Builds a `#context_snapshot{}` from cumulative state +
   `env.env_spec`.
2. `gen_server:call(SolutionGenerator, {generate, Snapshot})`.
3. `gen_server:call(CanonicalScorer, {score_body, Body, Seeds,
   HardWallSec})`.
4. Updates best/history; sends Submission to the caller (or
   appends to a returned list).

Holds no model context. The cumulative state is structured data
in process memory.

### SolutionGenerator

```erlang
-module(solution_generator).
-behaviour(gen_server).
-callback init([env()]) -> {ok, state()}.
-callback handle_call({generate, #context_snapshot{}}, _, state()) ->
    {reply, body :: binary(), state()}.
```

Per-call (or per-bench, configurable) gen_server. Fresh context
every `generate` — no memory across iters except what
`#context_snapshot{}` carries.

Inside the call: a bounded reasoning loop (§4), terminated by
wallclock deadline or convergence. Returns module source as a
binary.

### Runner (canonical scorer)

```erlang
-module(canonical_scorer).
-callback score_body(body :: binary(), seeds(), HardWallSec :: float()) ->
    #attempt_result{}.
```

Behaviour with two implementations:

- **`beam_canonical_scorer`** — production. Compiles the body
  to a module via `compile:forms/2`, loads it via
  `code:load_binary/3`, spawns one Erlang process per seed
  (monitored, with `max_heap_size` + a wallclock deadline),
  collects results, purges the module. See §5.
- **`fake_canonical_scorer`** — test. Scripted results from a
  fixture list.


## 3. Fitness functions

Architectural shape (three checks gate role separation):

- `test_when_orchestrator_run_called_then_yields_submissions/0`
- `test_when_solution_generator_generate_called_with_snapshot_then_returns_body_binary/0`
- `test_when_canonical_scorer_score_body_called_then_returns_attempt_result/0`

Domain quality:

```
best_score(Env, Cfg, T) = max { S#submission.score
                              | S <- orchestrator:run(Env, Cfg),
                                S#submission.walltime_sec =< T }
```

Live end-to-end (one check gates the whole chain):

- `test_when_bench_called_with_real_chain_then_returns_submission_with_solver_body_and_non_negative_score/0`
  — `body` parses as a valid Erlang module exporting `move/1`,
  `score` is a non-negative float.


## 4. SolutionGenerator runtime: Erlang, no SDK

A short Erlang gen_server. No external SDK, no tool-call JSON
gymnastics. The "tool" is implicit: every LLM turn, we run a dev
test on whatever code the model emitted; the result becomes the
next user message.

### Reasoning loop

```erlang
loop(Messages, Best, Deadline, Env) ->
    {ok, RespText} = llm_client:call(Env#env.model_client, Messages),
    Body = extract_fenced_erlang(RespText),
    {Score, Stdout} = dev_test(Body, Env),
    Best1 = case Score > Best#submission.score of
        true  -> #submission{body=Body, score=Score};
        false -> Best
    end,
    case time_left(Deadline) of
        T when T > ?MIN_ITER_TIME ->
            Observation = format_observation(Stdout, Score),
            Messages1 = Messages ++ [
                #{role => assistant, content => RespText},
                #{role => user,      content => Observation}
            ],
            loop(Messages1, Best1, Deadline, Env);
        _ ->
            Best1#submission.body
    end.
```

`?MIN_ITER_TIME` is conservative (~30s) — we stop with time to
spare so the last response actually arrives.

### Wallclock enforcement

Two-layer:

1. **Deadline param** passed by orchestrator. The loop checks
   `time_left(Deadline)` before each LLM turn.
2. **Top-level `erlang:send_after(DeadlineMs, self(), deadline)`**
   in `init/1`. A `handle_info(deadline, S)` returns `{stop,
   normal, S}` and the loop unwinds — the LLM call in progress
   completes, no body is corrupted.

No threads, no SIGTERM races. The BEAM is cooperative; we own
both ends of the cooperation.

### LLM client

`llm_client` is a thin hackney wrapper:

```erlang
call(Pid, Messages) ->
    gen_server:call(Pid, {chat, Messages}, infinity).

%% inside the gen_server:
handle_call({chat, Messages}, _, #state{base_url=U, key=K, model=M} = S) ->
    Body = jsx:encode(#{<<"model">> => M, <<"messages">> => Messages,
                        <<"temperature">> => 0.7}),
    Headers = [{<<"Authorization">>, <<"Bearer ", K/binary>>},
               {<<"Content-Type">>, <<"application/json">>}],
    {ok, 200, _, RespBody} = hackney:post(<<U/binary, "/v1/chat/completions">>,
                                          Headers, Body, [with_body]),
    #{<<"choices">> := [#{<<"message">> := #{<<"content">> := C}}|_]}
        = jsx:decode(RespBody, [return_maps]),
    {reply, {ok, C}, S}.
```

~15 lines. No streaming for now (`with_body` waits for full response).

### Dev test

`dev_test/2` is just `canonical_scorer:score_body/3` called with
the **dev seed range** (`?DEV_SEEDS`) instead of the canonical
held-out range. Same module, same BEAM, same compiled env —
only the seeds differ. The agent's observation is generated by
exactly the code that will score the final body; zero env drift.

```erlang
-define(DEV_SEEDS, lists:seq(2000, 2004)).  %% 5 dev games

dev_test(BodyBin, #env{canonical_scorer = Scorer}) ->
    AR = canonical_scorer:score_body(Scorer, BodyBin, ?DEV_SEEDS, 5.0),
    {AR#attempt_result.mean_score, format_stdout(AR)}.
```

The whole "dev test" is one call into the same `canonical_scorer`
behaviour the orchestrator uses. No port spawn, no docker, no
serialization — the Solver source goes from binary → compiled
module → spawned game process in one BEAM.

### Prompt shape

`env_spec` (built once by env loader) embeds:

1. **Task** — Solver behaviour contract:
   ```
   -module(submission).
   -export([move/1]).
   -spec move(board()) -> w | a | s | d.
   ```
2. **Output rule** — "Emit your module as a fenced
   ```` ```erlang ... ``` ```` block in your last assistant message.
   The harness reads the last fenced block."
3. **Budget hint** — `time_remaining_sec` from snapshot.

No tool registration, no JSON tool-call schemas. The agent writes
Erlang; we test it; we report results in the next user message.


## 5. Sandbox layers: outer docker, inner BEAM processes

Two layers, both load-bearing:

### Outer: one Docker image for the whole bench

`reward-bench-erl:0.1` is the deployment artifact. It pins:

- Erlang/OTP 27
- The compiled `reward_bench` release (all our modules:
  orchestrator, solution_generator, llm_client, canonical_scorer,
  env_2048, runner_canonical)
- `rebar.lock` deps (hackney, jsx) baked in

ENTRYPOINT is the release boot script. The container runs the
bench end-to-end; vLLM and stdout are the only things it talks
to. **One container per bench-run**, not per Solver.

This is purely a deployment / reproducibility boundary — no
per-Solver isolation work happens here. The image freezes a
known-good (Erlang version, bench code, lib deps) tuple so two
bench runs on different hosts produce comparable results.

### Inner: BEAM processes are the Solver sandbox

Solver code runs as ordinary Erlang processes inside the same
BEAM that runs the bench. We don't need kernel-level isolation
because the threat model is "LLM-generated code might be buggy",
not "adversarial actor". BEAM's process model gives us what we
actually need:

- **Crash isolation**: `spawn_monitor` per game seed; a Solver
  exception kills only that game's process. The
  `canonical_scorer` records the failed game and continues.
- **Memory cap**: `process_flag(max_heap_size, #{size => ...,
  kill => true})` on the game process — BEAM kills the process
  on overflow rather than letting it OOM the VM.
- **Wallclock cap**: `erlang:send_after(DeadlineMs, self(),
  {kill_game, MonitorRef})` plus monitor on the spawned process.
  When the timer fires we `exit(Pid, kill)`.
- **No filesystem / network access by accident**: the BEAM
  doesn't open files or sockets unless we call those modules.
  The `submission` module the LLM emits has `move/1` exported
  and that's the only call we make.

### Solver loading

```erlang
%% canonical_scorer.score_body/3 entry:
{ok, Module, Forms} = compile_solver(BodyBin),
{module, Module}    = code:load_binary(Module, "nofile", Forms),
Results = lists:map(
    fun(Seed) -> play_one_game(Module, Seed, HardWallSec) end,
    Seeds),
code:purge(Module),
code:delete(Module),
aggregate(Results).
```

No file ever written. `compile:forms/2` parses the binary source
to AST + bytecode; `code:load_binary/3` registers it. After
scoring we `purge` + `delete` so the next attempt starts clean.

### Binaries as messages

Bench-side Erlang code communicates only in **binaries, atoms,
integers, and records**. No file paths cross any process
boundary. The body — Erlang module source — is a `binary()` from
the moment `extract_fenced_erlang/1` lifts it from the LLM
response until `code:load_binary/3` registers it as bytecode in
the BEAM. No `submission.erl` file ever exists.

The only IO is HTTP to vLLM (hackney; binaries in, binaries out)
and stdout for logs. Path arithmetic above the Runner is
unrepresentable: there's nowhere to compute a path to.


## 6. Components

```
reward_bench/                       rebar3 project (single app)
├── src/
│   ├── reward_bench.app.src
│   ├── reward_bench_app.erl
│   ├── reward_bench_sup.erl
│   ├── bench.erl                   (use case — bench/2)
│   ├── orchestrator.erl            (gen_server)
│   ├── solution_generator.erl      (gen_server)
│   ├── llm_client.erl              (gen_server, hackney)
│   ├── canonical_scorer.erl        (behaviour)
│   ├── beam_canonical_scorer.erl   (production impl, in-VM)
│   ├── fake_canonical_scorer.erl   (test impl)
│   ├── extract_fenced_erlang.erl   (pure)
│   ├── compose_env_spec.erl        (pure)
│   ├── env_2048.erl                (game logic, pure)
│   ├── runner_canonical.erl        (plays one game w/ deadline+heap cap)
│   └── records.hrl
├── test/
│   ├── eunit/                      (unit tests)
│   └── *_SUITE.erl                 (Common Test integration + live)
├── tasks/
│   └── 2048/
│       └── SKILL_tier1.md          Erlang Solver contract
├── tests-spec/                     CATS markdown specs (unchanged tooling)
├── rebar.config
├── Dockerfile                      FROM erlang:27 + COPY release
└── Makefile                        rebar3 + docker build targets
```

Single rebar3 app (no umbrella needed — there's no second
deployable). Solver execution lives in `runner_canonical.erl`,
called by `beam_canonical_scorer` once per seed inside a
monitored process.

Per-app clean architecture: pure functions (`extract_fenced_erlang`,
`compose_env_spec`, `env_2048`) sit alongside gen_servers; the
behaviour-based seams (`canonical_scorer`, optionally
`llm_client`) allow fake adapters in tests.


## 7. Open items

- **Erlang Solver fidelity vs leaderboard history.** Existing
  Python baselines (`reference_fsm.py`) don't carry over; new
  baselines need to be written in Erlang and the leaderboard
  reset.
- **Game env parity.** `env_2048.erl` ports `env_2048.py`
  semantics including RNG and tile-spawn distribution. Property
  tests against the Python reference would help; deferred.
- **`hackney` vs `gun`.** Switch to `gun` if SSE streaming from
  vLLM becomes useful (lower latency to first token).
- **`temperature` is hardcoded.** Move to `bench_config()` when a
  second model is added that benefits from different sampling.


## 8. Cross-references

- [SPEC.md](SPEC.md) — lab contract (Solver shape, scoring rules,
  task definition).
- [`forge/AGENTS.md`](../../../AGENTS.md) — repo-wide rules; this
  file inherits Twain + Senior Erlang AI Engineer stance.
- [`apps/reward_bench/test/`](apps/reward_bench/test/) — unit
  + Common Test suites enforcing §§2-3, 5 invariants.

Forge phase reference: <https://www.opengroup.org/togaf>.
