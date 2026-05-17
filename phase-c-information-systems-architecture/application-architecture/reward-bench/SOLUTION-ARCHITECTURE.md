# reward-bench — Solution Architecture

How the SPEC contract is realised. SPEC describes *what*; this doc describes *how*.

## 1. Architectural overview

```
┌────────────────────────────────────────────────────────────────────┐
│  Orchestrator (host, Python — src/reward_bench/frameworks/main.py) │
│   - resolves ModelTarget from MODEL_REGISTRY (mirror of YAML)      │
│   - builds production ports (ModelClient, ToolRegistry, Parser,    │
│     Condenser, Supervisor, CanonicalScorer)                        │
│   - runs agent loop (src/tier1/agent_loop.py::run_loop)            │
│   - promotes last-good execute_submission body to submission.py    │
│   - hands off to CanonicalScorerPort for final scoring             │
│   - emits AttemptResult (sentinel on malformed submission)         │
│   - writes artifacts to ${STORAGE_ROOT}/labs/reward-bench/...      │
└──────────────────┬──────────────────────────────────┬──────────────┘
                   │                                  │
       inference   │ HTTPS                            │ docker run --rm
   (chat / tools / │ ${INFERENCE_BASE_URL}            │ --network=none
    condenser /    │                                  │ --memory=2g
    supervisor)    ▼                                  │ --pids-limit=256
  ┌──────────────────────────┐                        │ --cpus=N/2
  │  vLLM container          │                        ▼
  │  (provisioned externally │  ┌─────────────────────────────────────┐
  │   by wiki-compiler or    │  │ Per-attempt sandbox                 │
  │   inference mode)        │  │ reward-bench-tier1:${VERSION}       │
  │                          │  │  /workspace/submission.py  (rw)     │
  │  serves model under      │  │  /env/env_2048.py          (ro)     │
  │  test + condenser +      │  │  /reports/                 (rw)     │
  │  supervisor              │  │  runs runner_canonical.py           │
  └──────────────────────────┘  │  mp.Pool(cpu_count()) over seeds    │
                                │  honours REWARD_BENCH_* env vars    │
                                └────────────┬────────────────────────┘
                                             │ result.json + events.jsonl
                                             ▼
                       ${STORAGE_ROOT}/labs/reward-bench/experiments/<run_id>/
```

Single vLLM endpoint serves three roles: bench model under test, condenser, supervisor (see §6).

## 2. Components

| Component | Module path | Role |
|---|---|---|
| **Orchestrator** | `src/reward_bench/frameworks/main.py` | Composition root. Resolves `ModelTarget`, wires ports, invokes loop and scorer, marshals `AttemptResult`. |
| **Agent loop** | `src/tier1/agent_loop.py::run_loop` | Reads model reply via `ProtocolParser`, dispatches tool calls via `ToolRegistry`, feeds observations back, calls `CondenserPort` and `SupervisorPort` between turns. Knows nothing about HTTP, Docker, or specific tool implementations. |
| **Canonical scorer (Docker)** | `src/tier1/adapters/docker_canonical_scorer.py` | Implements `CanonicalScorerPort`. Spawns `reward-bench-tier1:${VERSION}`, reads `/reports/result.json`, maps to `AttemptResult`. Used for both final canonical scoring (20 seeds) and the `execute_submission` dev runner (5 seeds). |
| **Inference provisioning** | external (`wiki-compiler` mode or `inference` mode) | vLLM container at `${INFERENCE_BASE_URL}` is a prerequisite, not provisioned by this lab. Orchestrator calls it as a client. |
| **Condenser** | `src/reward_bench/adapters/llm_condenser.py` | Implements `CondenserPort`. Collapses older turns to a summary via the bench-model endpoint when input tokens cross the trigger threshold. `keep_recent` preserves the tail verbatim. |
| **Supervisor** | `src/reward_bench/adapters/llm_supervisor.py` | Implements `SupervisorPort`. Every `supervisor_every_k` iterations, posts `(iter, dev_mean, max_tile, walltime)` sweep tuples to the bench-model endpoint and parses a `SupervisorDecision`. If `stop_recommended`, injects a `finish` call. Replaces mechanical `max_no_improve`. |

## 3. Port discipline

Per the runtime-boundary rule, every dependency that crosses a runtime boundary (network, subprocess, Docker, file system depending on host state, OS process state) has: Protocol under `src/ports/`, production adapter, in-memory Fake under `src/adapters/fakes/`, and (if it has side effects) an autouse conftest binding.

| Port | Production adapter | Default test binding | Role |
|---|---|---|---|
| `CanonicalScorerPort` | `DockerCanonicalScorer` | `FakeCanonicalScorer` (autouse) | Score a `submission.py` over a seed list inside a sandbox; return `AttemptResult`. Backs both canonical and dev. |
| `InferenceOrchestrator` | external mode (`wiki-compiler` / `inference`) | n/a — `ModelClient` faked instead | Provision and serve the model at `${INFERENCE_BASE_URL}`. Out of scope for this lab. |
| `Tool` | `ViewTool`, `ExecuteSubmissionTool`, `FinishTool` | recording fakes per-test | Single unit of side-effectful action invoked from a reply. |
| `ToolRegistry` | `Tier1ToolRegistry` | inline `RecordingRegistry` (autouse via `fake_execute_tool`) | Owns the per-tier tool catalogue + schemas; dispatches by name. Tier 2-4 swap their own registry. |
| `ProtocolParser` | `CompositeParser([FencedTextParser, StructuredOpenAIParser])` | trivial recorder (autouse via `fake_execute_tool`) | Decode `AssistantReply` into `list[ToolCall]`. Fenced wins when both present; structured is the Mistral-family fallback. |
| `ModelClient` | `VllmOpenAIClient` | `FakeModelClient` (autouse) | OpenAI chat-completions call against vLLM with `tools=[...]` advertised. |
| `SupervisorPort` | `LlmSupervisor` | `NullSupervisor` (default) | `judge(sweep) -> SupervisorDecision`. |
| `CondenserPort` | `LlmCondenser` | `NullCondenser` (default) | Compact older turns when input tokens cross trigger. |
| `CpuCountPort` | `MultiprocessingCpuCount` | `FixedCpuCount(N)` (DI param) | OS-process state seam so use cases don't import `os.cpu_count`. |

Architecture test `tests/architecture/test_runtime_boundary_ports.py` asserts the manifest is complete (port file, adapter file, fake file, autouse binding) and fails on drift.

## 4. Runtime architecture (Docker sandbox)

Layer 2 (Docker) is the production path for **both** canonical scoring and the in-loop `execute_submission` dev runner. The legacy in-process Layer 1 (`InProcessCanonicalScorer`) remains for hermetic algorithm tests only.

### Docker invocation

```
docker run --rm \
  --network=none \
  --memory=2g \
  --pids-limit=256 \
  --cpus=${CANONICAL_CPUS} \                # host-side: cpu_count() // 2
  -v <workspace>:/workspace \               # rw — submission.py promoted
  -v <env_dir>:/env:ro \                    # ro — env_2048.py
  -v <reports_dir>:/reports \               # rw — result.json, events.jsonl
  -e REWARD_BENCH_NUM_GAMES=20 \
  -e REWARD_BENCH_SEED_BASE=1000 \
  -e REWARD_BENCH_STAGNATION_SEC=60 \
  -e REWARD_BENCH_HARD_WALL_SEC=300 \
  -e REWARD_BENCH_MOVES_STAGNATION=...      # optional move-count guard
  reward-bench-tier1:${VERSION}
```

`--network=none` is mandatory at tier 1 (anti-exfil). Tier 2-4 swap to `--network proxy-net` with iptables egress restricted to `${INFERENCE_DOMAIN}` (per SPEC); the same `CanonicalScorerPort` shape applies — only the network policy and image change.

### CPU policy

Host side: `--cpus=N` is the only knob, picked as `port.cpu_count() // 2` from `CpuCountPort`. Container side: `runner_canonical.py` runs `multiprocessing.Pool(processes=cpu_count())` — `mp.cpu_count()` reads the cgroup CPU quota, so the container uses exactly the slice Docker gave it. No `max_workers` threads through the codebase.

### Walltime enforcement

`hard_wall_sec` is enforced **by Docker**, not Python. `docker stop --time=N` issues SIGTERM then SIGKILL. A Solver wedged in a tight Python loop dies at the OS level. The in-container per-game stagnation detector (60 s of no `score` or `max_tile` change) handles the common case and writes `final_state="stagnated"`.

### Env-var contract (orchestrator → container)

| Env var | Default | Purpose |
|---|---|---|
| `REWARD_BENCH_NUM_GAMES` | 20 (canonical) / 5 (dev) | Number of seeded games to play. |
| `REWARD_BENCH_SEED_BASE` | 1000 | Starting seed; `[base, base+1, ..., base+N-1]`. |
| `REWARD_BENCH_STAGNATION_SEC` | 60 | Per-game progress watchdog inside the container. |
| `REWARD_BENCH_HARD_WALL_SEC` | 300 (canonical) / 75 (dev) / 60 (smoke) | Aggregate Docker walltime cap. 0 = disabled. |
| `REWARD_BENCH_MOVES_STAGNATION` | (set per run) | Move-count guard complementing the time-based detector. |

### dev/canonical alignment

`dev_hard_wall_sec = canonical_hard_wall_sec * 5 / len(canonical_seeds)`. With canonical=300 and 20 seeds, dev=75 s — keeps dev observations proportional to canonical scoring.

## 5. Cross-cutting decisions

Compressed from the 15 ADRs. ADR numbers retained as audit pointers.

- **Same model for bench + condenser + supervisor** (0001). One vLLM endpoint, one `ModelTarget`. `CondenserConfig.model_id` and `LlmSupervisor` both default to the bench `ModelTarget.id`. Eliminates a second container, a second registry entry, and the "model A had a better condenser" confound. Each model summarises and judges itself.
- **Malformed submission → sentinel `AttemptResult`, never raise** (0002). `main()` catches `FileNotFoundError` (no submission written) and `AttributeError` on `module.Solver` (no `Solver` class) and returns `AttemptResult(n_games=0, games=(), mean_score=0.0, ...)`. The discriminator is `n_games == 0`. Any other exception propagates as infra failure. Lets 21-model campaigns survive one bad submission.
- **Canonical bench defaults** (0003, 0015): `max_iters=500`, `n_trials=10`, `temperature=0.7`, `max_model_len=131072`, `max_no_improve=999999`, `finish_floor=0`, `hard_wall_sec=300`. Lives as a frozen `BenchConfig` value object (`src/reward_bench/entities/bench_config.py`); every leaderboard publication reports it. T=0.7 only affects Stage-1 author sampling — Stage-2 `Solver.move` is greedy by construction, so canonical scoring stays deterministic.
- **Condenser trigger at ~80 % of effective input budget** (0004). `_CONDENSER_TRIGGER_TOKENS = 80000` in `main.py`, derived as `0.8 × (131072 − 32768) ≈ 78643`, rounded up. ~18 K headroom for the last pre-compaction turn. 4-chars-per-token heuristic; future cycle will derive per-model from `ModelTarget.max_model_len`.
- **Plateau detection asks the bench model itself** (0005). `SupervisorPort.judge(sweep)` posts recent `(iter, dev_mean, max_tile, walltime)` tuples and parses `{"plateau": bool, "reasoning": str, "stop_recommended": bool}` with a conservative-bias prompt. Fires every `supervisor_every_k` turns (default 5). On `stop_recommended`, the loop injects `finish(note=reasoning)`. Replaces brittle threshold-based `max_no_improve`.
- **Docker sandbox + walltime budget** (0006, 0015). All scoring (canonical and dev) goes through `CanonicalScorerPort` → `DockerCanonicalScorer`. `--network=none`, `--memory=2g`, `--pids-limit=256`, `--cpus=N/2`. Hard kill via cgroup. Image digest pinned in `meta.json` for reproducibility.
- **`execute_submission` tool runs in Docker** (0008). Single sandboxed tool replaces the old `write_file` + `bash dev_runner` pair. The model emits the full submission body inline; the tool writes it to a transient container path, runs the dev runner on 5 seeds, returns a structured JSON observation (per-seed scores, max-tile, protocol violations, runtime tracebacks). NEVER raises — failures surface as fields. At `finish`, the LAST body that produced `per_seed != []` is promoted to host `/workspace/submission.py` for canonical scoring.
- **Smoke convention: early-stop on first `dev_mean > 0`** (0009). `SMOKE_CONFIG`: `max_iters=100`, `n_trials=1`, `T=0.7`, `hard_wall_sec=60`, `supervisor_every_k=0`, `smoke_early_stop=True`. Canonical scoring skipped — the smoke signal *is* the verdict. A `0.0` / `None` is a bench-side bug signal, never a model verdict. Per-model wall ~3 min on warm vLLM.
- **Mistral-family routes through structured tool_calls** (0010). Mistral / devstral / gpt-oss emit `[TOOL_CALLS]` which vLLM's `--tool-call-parser mistral` converts to OpenAI structured `message.tool_calls`; `message.content` is stripped. `_call_model` therefore advertises `tools=TOOL_SCHEMAS` on every request. `CompositeParser` reads both surfaces: `FencedTextParser` over `message.content` wins when both are present; `StructuredOpenAIParser` over `message.tool_calls` is the fallback. The structured parser strips U+0120 / U+2581 SentencePiece leaks from `function.arguments` before `json.loads`.
- **Ports for `ModelClient` / `ToolRegistry` / `ProtocolParser`** (0011, 0018). `run_loop` no longer imports `urllib.request`, hardcodes tool schemas, or knows about two parser surfaces. It orchestrates `client.call → parser.extract → registry.dispatch`. New tier surface = `ToolRegistry` swap. New model API = new `ModelClient` adapter. New protocol = new `ProtocolParser` adapter. The discipline generalises to every runtime boundary (ADR-0018 manifest).
- **Fakes + autouse for offline testing** (0012, 0014). `FakeModelClient` returns scripted `AssistantReply` values; `FakeCanonicalScorer` returns scripted `AttemptResult`s. `tests/conftest.py` autouse fixture binds Fakes unless the test is marked `live` (real production stack) or `no_fake` (real code, hermetic sandbox). Every `test_spec` MUST declare a *Model client injection point* subsection naming the seam, default mode, and override mechanism. CI runs the suite via fakes in ~3 s; live-marked tests run on demand.
- **`models.yml` is the source of truth; `MODEL_REGISTRY` is a mirror smell** (0013). `wiki-compiler/configs/models.yml` is canonical. `src/reward_bench/use_cases/model_registry.py::MODEL_REGISTRY` is being rewritten as a thin wrapper that loads the YAML at import time (via `run_battery.load_models`), filters `bench_skip: true`, and maps to `ModelTarget`. The hand-maintained Python literal is queued for deletion — currently both coexist with observed drift.

## 6. Source-of-truth collapse: same vLLM endpoint serves three roles

The condenser (ADR-0001), supervisor (ADR-0005), and bench model all hit the same `${INFERENCE_BASE_URL}` with the same `ModelTarget`. Concrete consequences:

- One container, one GPU mutex, one `MODEL_REGISTRY` entry.
- A/B comparisons are end-to-end including each model's self-summarisation and self-judgment behaviour.
- A model that can't summarise its own context or judge its own progress *should* score worse — that's signal, not noise.
- Condenser and supervisor cost extra inferences; mitigated by trigger thresholds (`trigger_tokens=80000`, `supervisor_every_k=5`).

## 7. Open items / known tensions

- **Bench bug — zero-score artifacts from bench-spawned Docker.** Live test reproduces it; canonical Docker invocations sometimes return `score=0` artifacts despite a working submission. Under investigation; suspected in the canonical scorer path, not the model.
- **`MODEL_REGISTRY` duplication.** YAML and Python tuple disagree (e.g. `qwen3.6-27b-awq` vs `qwen3.6-27b-awq-int4-community`, missing `qwen3.6-35b-a3b-fp8`). Rewrite to load-from-YAML pending (ADR-0013 cycle 101).
- **Condenser token estimation is heuristic.** 4-chars-per-token may be off ±30 %. Trigger has 18 K headroom; future cycle to lift `trigger_tokens` onto `BenchConfig` per `ModelTarget.max_model_len`.
- **`validate_submission_protocol`** still calls `instance.move(test_board)` in the bench main thread — same wedge pattern Layer 2 fixed elsewhere. Future cycle wraps it in `multiprocessing.Process` with hard timeout.
- **`max_iters=500` blows past 128 K** on long conversations. Condenser must function for the full canonical defaults to be achievable end-to-end; long runs await condenser hardening.
- **Static submission protocol is not implemented.** SPEC describes it; only the interactive tool-using agent loop currently exists.
- **Tier 2-4 ports.** Future tier runners (LangGraph, orchestrator) will follow the ADR-0018 Port + Fake + autouse pattern; not yet added to the manifest.

## 8. Cross-references

### Lab docs
- `SPEC.md` — contract this implementation realises.
- `CATS.md` — testing/spec discipline (specs language-agnostic; injection-point rule from ADR-0014).
- `AGENTS.md` — operating runbook.

### Source-code anchors
- `src/reward_bench/frameworks/main.py` — orchestrator / composition root. Holds `_CONDENSER_TRIGGER_TOKENS`, sentinel construction.
- `src/reward_bench/frameworks/run_battery.py` — `make reward-battery` driver; reads `models.yml`.
- `src/tier1/agent_loop.py` — `run_loop`, `_call_model` (transitional), tool dispatch.
- `src/tier1/adapters/docker_canonical_scorer.py` — `DockerCanonicalScorer` (production).
- `src/adapters/in_process_canonical_scorer.py` — Layer-1 hermetic scorer (testing only).
- `src/adapters/parsers/fenced_text_parser.py`, `structured_openai_parser.py` — the two protocol surfaces.
- `src/adapters/fakes/` — `FakeModelClient`, `FakeCanonicalScorer`, etc.
- `src/ports/` — `model_client.py`, `tool_registry.py`, `protocol_parser.py`, `canonical_scorer.py`, `supervisor.py`, `condenser.py`, `cpu_count.py`.
- `src/reward_bench/entities/bench_config.py` — frozen `BenchConfig` value object.
- `src/reward_bench/entities/condenser_config.py`, `supervisor_decision.py`.
- `src/reward_bench/adapters/llm_condenser.py`, `llm_supervisor.py`, `null_condenser.py`, `null_supervisor.py`.
- `src/reward_bench/use_cases/model_registry.py` — `MODEL_REGISTRY` (YAML mirror, smell).
- `tasks/2048/runner_canonical.py` — in-container runner; reads `REWARD_BENCH_*` env vars.
- `tasks/2048/env.py` — `GameBoard` (lifted from rl-2048).
- `Dockerfile.tier1` — `reward-bench-tier1:${VERSION}` image.
- `tests/architecture/test_runtime_boundary_ports.py` — ADR-0018 manifest enforcement.
- `tests/conftest.py` — autouse Fake bindings.
- `wiki-compiler/configs/models.yml` — canonical model registry.

### Upstream forge ADRs
- Forge ADR 0028 — inference mode (single vLLM endpoint pattern).
- Forge ADR 0029 — reward-bench (parent design).
- Forge ADR 0015 — verifiable agent rewards (first principle this lab realises).
- Wiki-compiler ADR 0008 — model-registry single source of truth.
