# reward-bench — agentic comprehensiveness benchmark

## Purpose

Server-side, Docker-sandboxed evaluator that runs a candidate LLM through a 4-tier ladder of agentic puzzle-solving tasks. Each tier asks the model to produce an FSM (or FSM-of-agents) that maximises a verifiable quantitative reward on a target task. The first task is 2048; the harness is built to admit additional tasks later (each as a self-contained module).

reward-bench is **the comprehensiveness scoreboard** for forge. Throughput is measured separately (`bench-fp8-16k.sh`, `bench-nvfp4-16k.sh`). reward-bench answers: "given a model that's fast enough, can it actually orchestrate to solve a task?"

Per [ADR 0029](../../../phase-preliminary/adr/0029-reward-bench.md). Per [ADR 0015](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md), scores are verifiable — derived from the env's deterministic reward function, not from any judge.

## Non-goals

- Not a training lab. Training is `rl-2048`'s job (Jupyter + GRPO + Unsloth + CUDA). reward-bench is CPU-only evaluation with pinned Docker images.
- Not a UI. Headless. `make reward-bench MODEL=<id> TIER=1 TASK=2048` runs one attempt and exits.
- Not coupled to one task. The harness is task-agnostic; today only 2048 is wired in.
- Not a model server. We consume the vLLM endpoint at `${INFERENCE_DOMAIN}` from whichever lab/mode is currently up.

## Architecture

### Layered structure

```
┌─────────────────────────────────────────────────────┐
│  orchestrator (host, Python)                        │
│   - picks model from models.yml                     │
│   - sends tier-N prompt to vLLM                     │
│   - extracts submission from response               │
│   - runs static anti-cheat (AST + bandit)           │
│   - launches per-attempt Docker container           │
│   - replay-determinism check (second container)     │
│   - writes artifacts                                │
└─────────────────────────────────────────────────────┘
              │
              ▼ (docker run)
┌─────────────────────────────────────────────────────┐
│  tier-N sandbox (Docker, immutable image)           │
│   - mounts /env (ro) /workspace (rw) /reports (rw)  │
│   - runs runner.py from /env                        │
│   - runner imports submission, plays N games        │
│   - writes /reports/result.json                     │
│   - tier 1: --network=none                          │
│   - tier 2-4: --network proxy-net + iptables-egress │
│               only ${INFERENCE_DOMAIN}              │
└─────────────────────────────────────────────────────┘
              │
              ▼ (artifact copy)
${STORAGE_ROOT}/labs/reward-bench/experiments/<run_id>/
```

### Container topology

One container per attempt, image `reward-bench-tier${N}:${VERSION}` (built from local `Dockerfile.tier${N}`). Image base is `python:3.12-slim` plus tier-specific packages (see ADR 0029 §8). No host home, no docker socket, no `/var/log`. `proxy-net` only for tier 2+ (not tier 1).

### Mode mutex

CPU-only — co-runs with whichever mode/lab is currently providing inference. Required prerequisite: `${INFERENCE_DOMAIN}` is reachable from the proxy-net network (i.e., one of `wiki-compiler` mode / `inference` mode is up and serving the candidate model).

### Reuse from rl-2048

The 2048 env (`tasks/2048/env.py`) is lifted from the `GameBoard` class in `rl-2048/notebooks/2048_gpt_oss_20b.ipynb` — same WASD action API, same seed/target/probability_fours params. The anti-cheat helpers (`check_python_modules`, `create_locked_down_function`) are adapted from the same notebook (which uses Unsloth's helpers; reward-bench reimplements without the Unsloth dep so the sandbox stays minimal).

This guarantees a model fine-tuned on rl-2048 sees the same env at eval time — no environment drift between training and benchmark.

## Data contracts

### Required env (read from forge `.env`)

- `STORAGE_ROOT` — data-disk root, matches forge.
- `INFERENCE_BASE_URL` — vLLM endpoint, e.g. `https://inference.mikhailov.tech/v1`.
- `VLLM_API_KEY` — same value as in `forge/.env`.
- `INFERENCE_ACTIVE_MODEL_ID` — id from `wiki-compiler/configs/models.yml`; the model under test.

### Per-attempt directory layout

```
${STORAGE_ROOT}/labs/reward-bench/experiments/<run_id>/
  meta.json               # see schema below
  prompt.txt              # the prompt sent to the model
  raw_response.txt        # the model's full text response
  submission.py           # extracted Python (tier 1) or graph spec (tier 2+)
  submission.sha256       # for replay verification
  cheat-check.json        # AST + bandit findings
  events.jsonl            # per-game step trace
  result.json             # final scores
  result-replay.json      # second-run scores (must match within tier tolerance)
  sandbox.log             # container stdout/stderr
  done                    # touch-marker — presence = run finalised
```

### Schemas (pydantic v2)

```python
# meta.json
class AttemptMeta(BaseModel):
    run_id: str                # e.g. "2026-05-04-180423-qwen36-27b-fp8-tier1"
    model_id: str              # from models.yml
    served_model_name: str     # what vLLM advertises
    task_id: Literal["2048"]   # extensible
    tier: int = Field(ge=1, le=4)
    started_at: datetime
    image_digest: str          # sha256 of sandbox image (for reproducibility)
    forge_commit: str          # forge git rev at attempt time

# result.json
class GameResult(BaseModel):
    seed: int
    score: int = Field(ge=0)
    max_tile: int = Field(ge=2)
    moves: int = Field(ge=0)
    final_state: Literal[
        "won", "lost", "max_moves",
        "stagnated",                 # neither score nor max-tile changed for stagnation_sec
        "walltime_exceeded",         # outer hard-wall cap fired (only if HARD_WALL_SEC>0)
        "solver_error", "invalid_action",
    ]
    walltime_sec: float

class AttemptResult(BaseModel):
    games: list[GameResult]
    mean_score: float
    median_score: float
    std_score: float
    max_max_tile: int
    n_games: int
    aggregate_walltime_sec: float
    stagnation_sec: float        # default 60 — per-game progress watchdog
    hard_wall_sec: float         # 0 = disabled. Outer runaway-protection cap.
    stagnated_any: bool          # any game ended in final_state="stagnated"
    walltime_exceeded: bool      # any game ended due to outer hard-wall cap

# cheat-check.json
class CheatFinding(BaseModel):
    layer: Literal["ast", "bandit"]
    severity: Literal["info", "warning", "rejected"]
    rule: str                  # e.g. "no_subprocess"
    line: int
    code: str

class CheatReport(BaseModel):
    findings: list[CheatFinding]
    network_policy: Literal["none", "vllm_only"]
    replay_score_match: bool | None
    replay_tolerance_pct: float
    verdict: Literal["clean", "warning", "rejected"]
    rejected_reason: str | None
```

## Submission protocols

Each tier admits two protocols for getting from a model to a scored
submission. Both target the same per-tier submission file (Solver
class, build_graph, or construct meta-orchestrator) described in the
tier sections below. They differ only in how the model produces it.

### Static — single-reply emission

The model receives the task spec in one prompt and must emit the
submission as one fenced code block in its reply. The harness extracts
the block, writes it to the sandbox, runs the game suite, scores.

Status: planned. Not currently implemented.

### Interactive — tool-using agent loop

The model is given a workspace, an env module, and a tool protocol. It
reads files (view), submits code for evaluation (execute_submission),
and signals completion (finish). The loop runs up to a per-attempt
iteration cap or until the model calls finish. The submission body
from the most recent successful `execute_submission` call is what gets
scored at finish time (the bench promotes it into the final
`/workspace/submission.py`).

Tool-call wire format: each call is one fenced block in the assistant
reply:

    ```tool
    {"name": "<active-tool-name>", "args": {<...>}}
    ```

Active tool set (per [ADR 0008](docs/adr/0008-docker-sandboxed-execute-submission-tool.md)):
  - view(path)              read file contents into the next prompt.
  - execute_submission(content) write the submission body into a
                            sandboxed `reward-bench-tier${TIER}` Docker
                            container, run the dev-runner, return a
                            structured JSON observation
                            (per-seed scores, max-tile, protocol
                            violations, runtime tracebacks).
  - finish(note)            end the loop; the most recent
                            execute_submission body is promoted to
                            `/workspace/submission.py` for canonical
                            scoring.

The parser that decodes assistant replies into (name, args) tuples is
specified in spec/parser.md.

Status: the only currently-implemented protocol. The live 2026-05
reward-bench campaign runs every tier and every model in this mode.

### Why two protocols

Static bounds reasoning at one forward pass; it is the cheaper baseline.
Interactive gives the model access to the env source and shell iteration
on a larger context budget. Cross-mode comparison is informative.

## Tier specifications

### Tier 1 — closed-world FSM

**Image:** `reward-bench-tier1:${VERSION}` — base + numpy + transitions + pydantic.
**Network:** `--network=none`.
**Submission:** Python module with `class Solver` exposing `move(board: list[list[int]]) -> str` returning one of `'W' | 'A' | 'S' | 'D'`. The class MUST use the `transitions` library to declare states + transitions (we grep for `from transitions import` and reject otherwise — soft enforcement).
**Allowed imports:** numpy, transitions, re, math, random, collections, itertools, functools, dataclasses, typing, plus `env_2048` (the read-only env module).
**Reward:** mean game score over N=20 games (configurable).
**Replay tolerance:** 0 % — exact match required.
**Author-stage inference context:** the Stage 1 author loop runs the
model with **128 K input + output context** (`--max-model-len 131072`).
A **condenser** summarises older turns when prompt + reserved
output exceeds the budget so the loop can run as long as the model
can still make progress. This applies to the interactive submission
protocol; static-mode authors get one shot inside the same budget.

### Tier 2 — open-world FSM-of-agents

**Image:** `reward-bench-tier2:${VERSION}` — tier1 + langgraph + openai + tenacity + structlog.
**Network:** `--network proxy-net` + iptables egress restricted to `${INFERENCE_DOMAIN}`.
**Submission:** Python module exposing `def build_graph() -> langgraph.StateGraph`. Each node is a function that may call `llm.invoke(prompt) -> str` (provided shim wraps the openai client pinned to `${INFERENCE_BASE_URL}` and the active model). Nodes return state-update dicts.
**Allowed imports:** tier1 + `langgraph`, `langchain_core`, `pydantic`, `openai`, `tenacity`, `structlog`.
**Reward:** mean game score over N=10 games (fewer because LLM calls slow it).
**Replay tolerance:** 5 % — LLM micro-noise tolerated.

### Tier 3 — orchestrator-chosen edges

**Image:** `reward-bench-tier3:${VERSION}` — tier2 + openhands-sdk.
**Network:** same as tier 2.
**Submission:** A LangGraph + an orchestrator function that routes between nodes at runtime. The orchestrator function may make its own LLM call to decide the transition.
**Reward:** mean over N=10.
**Replay tolerance:** 5 %.

### Tier 4 — orchestrator constructs the FSM

**Image:** same as tier 3 (no new deps).
**Submission:** A meta-orchestrator function `def construct(task_spec) -> Solver` that, when called, returns a Solver instance. The Solver may itself contain dynamically-built LangGraph or OpenHands agents.
**Reward:** mean over N=10.
**Replay tolerance:** 10 % (more meta-randomness).

## Make targets

```
make reward-bench MODEL=<id> TIER=<N> TASK=<id>
    Run one attempt for one (model, tier, task) cell. Produces one
    artifact directory.

make reward-battery TIER=<N> [--filter <regex>]
    Iterate over every model in wiki-compiler/configs/models.yml with
    bench_tier ≠ skip; run one attempt at the given TIER for each.

make reward-bench-build
    Build all four sandbox Docker images, pinned by digest.

make reward-bench-down
    No-op (no long-running containers); included for symmetry with
    other labs. Removes any stale per-attempt containers if present.

make reward-bench-clean
    Delete all per-attempt artifacts older than N days (default: keep
    forever — admin-driven cleanup).
```

### Implementation extras

The Makefile additionally exposes operational helpers that are NOT
part of this contract — they evolved during development and stay
alongside the spec targets for convenience:

- `make smoke-tier1` — run the reference FSM through Stage 2 + Stage 3
  without an LLM. Used for CI/regression: builds the tier-1 image,
  plays 20 reference-FSM games, asserts mean_score and replay match.
- `make shim ROOT=<dir> PORT=<n>` — start the OpenAI-compatible Claude
  shim for fixture/dev runs without GPU.
- `make claude-fixture-tier1 RUN_ID=<x> SHIM=<url>` — drive the agent
  loop through the shim (Claude-in-the-loop fixture).

`make reward-battery` is currently a stub that exits non-zero — full
models.yml iteration is queued as a backlog item (cycle 94+). Cycle
78 ran the equivalent sweep manually via 22 per-model CATS tasks.

## Per-game stagnation detector

Stage 2 budgets are **per-game**, not per-attempt. Each game runs as long as it's making progress; "progress" means `game.score` increased OR `game.max_tile` increased. If neither has changed for `REWARD_BENCH_STAGNATION_SEC` seconds (default 60), the game ends with `final_state="stagnated"`. The score accumulated up to that point is kept.

- Tier-1 FSMs play 20 games in seconds (microseconds per move) — they never trip the detector.
- Tier-2+ candidates calling an LLM per move have 60 s ≈ 30-60 moves of headroom; if the policy can't find a merge in that span the game is genuinely stuck and we move on.
- Detection is wall-time-based, so it normalises across tiers without per-tier tuning.

An outer runaway cap remains available via `REWARD_BENCH_HARD_WALL_SEC` (default 0 = disabled). Set it to e.g. 1800 if you want to bound total Stage-2 wall time as a safety net for badly-misbehaving solvers.

Rationale: per-game stagnation is more honest than a hard wall budget. A submission that legitimately sustains long, productive games (the textbook expectimax case) shouldn't be punished by a one-size-fits-all clock; one that's stuck in a no-progress loop should be cut off fast regardless of decision latency.

## Risk surfaces

- **Sandbox escape via `pickle.loads`** — submissions could load a malicious pickle that does anything. Mitigation: AST scan rejects `pickle` import; bandit also flags this rule. If a submission needs serialisation, `json` is allow-listed.
- **AST-walk false positives** — a submission using `eval` for legitimate reasons (e.g., literal eval of board state). Mitigation: AST walk knows the difference between `eval(arbitrary_string)` (rejected) and `ast.literal_eval(arbitrary_string)` (allowed via the `ast` whitelist).
- **Replay non-determinism** in tiers 2-4 — vLLM's KV cache + speculative decoding can introduce ~0.1 % token-level noise even with `temperature=0`. Mitigation: per-tier replay tolerance (0 % tier 1, 5 % tier 2-3, 10 % tier 4). Submissions whose replay drifts more get verdict=`rejected`.
- **Iptables egress rule drift** — if proxy-net's iptables config changes (e.g., during caddy reconfig), tier 2-4 submissions might suddenly reach the open internet. Mitigation: smoke-tests verify the egress allowlist before each `reward-battery` run.
- **Score gaming via timing-based randomness** — a submission could read the wall-clock and use it as a seed (defeating replay determinism). Mitigation: AST scan flags `time.time()`, `datetime.now()`, `os.urandom`, `time.monotonic()` etc. — only `random.Random(seed)` and `numpy.random.default_rng(seed)` allowed.

## Cross-references

- [ADR 0029 — reward-bench](../../../phase-preliminary/adr/0029-reward-bench.md) — design decisions
- [ADR 0015 — verifiable agent rewards](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md) — first principle this lab realises
- [wiki-bench/SPEC](../wiki-bench/SPEC.md) — sibling lab, source of the Docker-sandbox pattern
- [wiki-bench/docs/adr/0002 — Docker sandbox](../wiki-bench/docs/adr/0002-docker-sandbox-and-storage-root.md) — the pattern we mirror
- [rl-2048/notebooks/2048_gpt_oss_20b.ipynb](../rl-2048/notebooks/2048_gpt_oss_20b.ipynb) — source of the `GameBoard` env we reuse

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: ADR 0029 — forge needs a verifiable comprehensiveness scoreboard.
- **Goal**: [Quality](../../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95).
- **Outcome**: this lab + 4-tier ladder + per-attempt artifacts; first task 2048; quantitative leaderboard across all models in registry.
- **Measurement source**: lab-tests: RB (reward-bench smoke + AGENTS Phase A-H integrity).
- **Contribution**: closes the throughput-only gap in model selection signal — comprehensiveness becomes diff-able.
- **Capability realised**: [Architecture knowledge management](../../../phase-b-business-architecture/capabilities/forge-level.md).
- **Function**: Provide-verifiable-comprehensiveness-signal-for-LLM-selection.
- **Element**: this directory.
