# ADR 0029 — reward-bench: agentic comprehensiveness benchmark with verifiable rewards

## Status

Accepted (2026-05-04). Active.

## Measurable motivation chain

Per [P7](../architecture-principles.md):

- **Driver**: forge needs a comprehensiveness signal for LLM models that goes beyond throughput. Existing options either lack verifiability (article-quality "vibe checks", LLM-as-judge), don't scale (human review of 200 outputs), or test the wrong thing (single-turn benchmarks like MMLU). Architect call: «agentic task solving is the best».
- **Goal**: [Quality](../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95). Picking a model based on throughput alone risks regressing wiki-compile output quality; we need an orthogonal signal that's still **verifiable** (per [ADR 0015](0015-verifiable-agent-rewards.md)).
- **Outcome**: a new `reward-bench` lab + this ADR + a 4-tier ladder of agentic puzzles with quantitative rewards. First task: 2048. Each candidate model writes (or assembles) an FSM-shaped solver; the lab runs it in a Docker sandbox; the score is the verifiable reward.
- **Measurement source**: lab-tests: RB (reward-bench smoke + AGENTS Phase A-H integrity).
- **Contribution**: closes the comprehensiveness-without-LLM-judge gap. Models become directly comparable on a quantitative scale that doesn't require subjective grading.
- **Capability realised**: [Architecture knowledge management](../../phase-b-business-architecture/capabilities/forge-level.md).
- **Function**: Provide-verifiable-comprehensiveness-signal-for-LLM-selection.

## Context

Existing forge benches:

- **wiki-bench** runs OpenHands agents against wiki-compile (real production task). Output is a wiki article. **No verifiable reward** — quality requires LLM-judge or human eyeball. Useful as a smoke test, not as a scoreboard.
- **wiki-bench microbench** (T1, T2, T3, T4 etc.) measures specific quality dimensions of compiler output. Verifiable per-axis but tied to one task and post-hoc on production runs.
- Throughput suite (`bench-fp8-16k.sh`, `bench-nvfp4-16k.sh`) measures tokens/sec per model — no quality signal at all.

Three observations forced the new bench:

1. The 2026-05-04 architect call: «agentic task solving is the best».  Single-turn answer benches (MMLU-like) don't capture the model's ability to *orchestrate* — and orchestration is what wiki-compile actually requires of the model in production.
2. The same call: «not verifiable rewards» (rejecting Claude-as-judge / regex / keyword scoring as a proxy for comprehensiveness). Forge's [ADR 0015](0015-verifiable-agent-rewards.md) makes verifiable rewards a first principle; comprehensiveness measurement must satisfy this constraint.
3. forge already has `rl-2048` with a working `GameBoard` env, anti-cheat primitives (Unsloth's `check_python_modules` + `create_locked_down_function`), and reward functions. The infrastructure for "model writes a solver, we score it" is half-built; we just need a benching wrapper around it.

## Decision

### 1. New lab — `reward-bench`

A sibling to `wiki-bench` at `phase-c-information-systems-architecture/application-architecture/reward-bench/`. Same Docker-sandbox pattern as wiki-bench (per its [ADR 0002](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0002-docker-sandbox-and-storage-root.md)) but specialised for *verifiable-reward agentic puzzles* rather than wiki-compile. Co-runs with whichever lab/mode provides the inference endpoint (wiki-compiler or inference); reward-bench is a CPU-only client.

### 2. Four-tier ladder of meta-FSM construction

Each tier shares the same target task (initially 2048, more later) and the same reward function (game score). Tiers differ by what the model has to produce:

| Tier | Submission shape | Runtime *inside* Docker | World |
|---|---|---|---|
| 1 | Python `class Solver` with `move(board) → action`. Internal structure: a `transitions.Machine` FSM. | python:3.12 + numpy + transitions | **closed** — no LLM calls during play; pure deterministic Python |
| 2 | `langgraph.StateGraph` where each node wraps an `llm.invoke()` call against the same model | tier1 + langgraph + scoped LLM client | open; LLM calls allowed only to `${INFERENCE_DOMAIN}` |
| 3 | OpenHands agent spec / config; orchestrator chooses transitions at runtime | tier2 + openhands-sdk | open; OpenHands action whitelist |
| 4 | Meta-program that *constructs* the FSM at runtime per task instance | tier3 (OpenHands as meta-orchestrator) | open + recursive (depth-limited) |

The tier ladder tests increasing meta-coding ability. A model competent at tier 1 may not have learned LangGraph well enough for tier 2; a model fluent in agent frameworks may still fail at tier 4's program-synthesis step.

### 3. Docker is the outer wrapper for **all** tiers

Per-tier Docker images differ in their *contents*, but Docker remains the outer boundary uniformly because it gives us:

- **Resource caps**: 2 GB RAM, 2 CPU, 600 s walltime, 256 PIDs (cgroups).
- **Reproducibility**: image pinned by sha256 digest; same digest + same submission + same seeds = identical score (tier 1) or near-identical (tiers 2-4 with `temperature=0` + seeded LLM).
- **Anti-cheat surface**:
  - `--network=none` (tier 1) or `--network proxy-net` + iptables egress allowlist to `${INFERENCE_DOMAIN}` only (tiers 2-4).
  - Read-only `/env` mount (env source code; submission can `import` but cannot read the score-computing logic to tamper with it).
  - Read-write `/workspace` only (submission lives here); no host home, no docker socket.
  - Non-root user (UID 1000); dropped capabilities (only CHOWN/SETUID/SETGID retained).

### 4. Anti-cheat — three-layer strategy

1. **Pre-flight static check on the submission** (host-side):
   - **AST walk** — reject imports outside an allow-list; reject `__import__`, `eval`, `exec` of strings, raw `compile`, `open()` writes outside `/workspace`, `subprocess`, `socket`, `urllib`, `requests`, `pickle.loads` (deserialise).
   - **`bandit` static security scan** — extra rule coverage (e.g., `os.system`, `shell=True`, `tempfile.mktemp` race).
   - Whitelist for tier-1 imports: `numpy`, `transitions`, `re`, `math`, `random`, `collections`, `itertools`, `functools`, `dataclasses`, `typing`, plus the task-supplied env. Whitelist extends per-tier (tier 2 adds `langgraph`, `pydantic`, `openai`; tier 3 adds `openhands_sdk`).
2. **Network isolation enforced by Docker**, not by the AST scan. Even if a submission imports `socket` undetected, `--network=none` (tier 1) means there's nothing to talk to. Tier 2-4 use a proxy-net + iptables egress rule that allows only `${INFERENCE_DOMAIN}`.
3. **Replay-determinism check** — after a successful run, the harness re-runs the submission in a fresh container with the same seed. Tier 1: scores must match exactly. Tiers 2-4: with `temperature=0` + `seed=N` on vLLM, scores are deterministic-ish (vLLM's KV-cache + speculative decoding can introduce ~0.1 % token-level noise; we tolerate ≤ 5 % score variance, larger = flagged).

### 5. Per-attempt artifacts

`/mnt/steam/forge/labs/reward-bench/experiments/<run_id>/`:

```
meta.json               # model_id, task_id, tier, started_at, image_digest
prompt.txt              # the prompt sent to the model
raw_response.txt        # the model's full response
submission.py           # extracted Python code (tier 1) or config blob (tier 2-4)
submission.sha256       # for replay verification
cheat-check.json        # AST + bandit findings
result.json             # {games: [...], mean_score, median, max_max_tile, walltime}
result-replay.json      # second-run result (must match)
events.jsonl            # every game step (action, board, reward); tier 2+ also LLM call traces
sandbox.log             # container stdout/stderr
done                    # marker — presence = run finalised (ok | rejected | failed)
```

### 6. Reuse rl-2048 primitives

- `GameBoard` from `rl-2048/notebooks/2048_gpt_oss_20b.ipynb` — has size + seed + target + probability_fours params; WASD action API. Lift into `reward-bench/tasks/2048/env.py` (cleaned, typed with pydantic where helpful).
- `check_python_modules` and `create_locked_down_function` (Unsloth helpers) — adopt as the AST-walk implementation behind layer 1 of anti-cheat.
- `extract_function`, `function_works`, `no_cheating`, `strategy_succeeds` reward fns — same pattern for tier 1.

This avoids re-deriving the same logic and keeps rl-2048 (training) and reward-bench (eval) using compatible primitives — the same model that learns on rl-2048 can be evaluated on reward-bench without environment drift.

### 7. Two-stage harness — author (with ralph loop) + canonical eval

Per-attempt flow:

```
Stage 1 — AUTHOR (with ralph loop)
  Sandbox A (Docker, agent runtime).
  The candidate model receives /tasks/2048/tier-1/SKILL.md and tools:
    - file_editor (write/edit submission.py in /workspace)
    - bash (run /tasks/2048/dev_runner.py /workspace/submission.py for fast feedback)
    - view, finish
  The agent iterates: write → run dev_runner on dev seeds (1..5) → observe
  score → refine → repeat. Until 'finish' or budget (N iterations / M wall).
  Implementation: the harness ships a minimal-agent-loop (~150 LOC) — a
  single-purpose script that reads SKILL.md, calls /v1/chat/completions,
  parses tool calls, executes, loops. This is lighter than OpenHands.
  Wiki-bench's full OpenHands harness can be wired in later for Tiers 3-4
  if/when the tier ladder shows we need it.

Stage 2 — CANONICAL EVAL
  Sandbox B (Docker, fresh container; Dockerfile.tier1).
  --network=none. No bash, no edit tools.
  Mounts: /env (ro), /workspace/submission.py (ro), /reports (rw).
  Runs runner_tier1.py against canonical seeds 1000..1019 (held-out).
  Plays 20 games at target=2048, max_moves=10000.
  Writes /reports/result.json + /reports/events.jsonl.

Stage 3 — REPLAY (anti-cheat)
  Same as Stage 2 in another fresh container, same seeds.
  Tier 1: scores must match exactly (closed-world is deterministic).
  Tiers 2-4 (later): tolerance per ADR §4.
```

**Dev/test seed split** keeps the canonical eval honest. Agent develops
against `1..5`; harness scores on `1000..1019`; replay uses the same
canonical seeds (determinism is checked, not generalisation).

### 8. Harness validation via Claude-shim fixture

Before pointing the harness at vLLM-served candidate models, we validate
the full pipeline end-to-end with a fixture that routes `/v1/chat/completions`
to the harness author (Claude in the Cowork session) instead of an LLM.
Per-request, the shim writes the prompt to `prompts/turn-NNN.json`, polls
for `responses/turn-NNN.json`, returns it OpenAI-format. The shim is
in-tree at `reward-bench/bin/claude_shim.py`. This:

- Validates the entire flow (agent loop, ralph iteration, AST anti-cheat,
  Stage-2 runner, replay determinism) without burning GPU time.
- Establishes a **ceiling reference** for the leaderboard. My (Claude's)
  attempt scores some number — call it C. Every subsequent candidate model
  is reported alongside C as "fraction of ceiling reached".
- Catches harness bugs (broken SKILL.md, wrong sandbox config, dev_runner
  contract drift) BEFORE we throw GPU time at 12 candidate models.

Per [Shannon-style information capacity scaling] — a 27B model at NVFP4
holds ~100 Gbits of parametric information; a frontier-class system holds
~80×. Tier-4 program-synthesis tests are likely to land above the
information ceiling of every model in the candidate set; that's a
*feature* of the bench, not a flaw — it gives the leaderboard a clear
top-bound and reveals where each parameter scale taps out.

### 9. Build sequencing

1. **Phase 1 (this commit):** ADR + SPEC + lab dirs + Dockerfile.tier1 + harness files; deploy to forge tree.
2. **Phase 2:** Build Dockerfile.tier1 image; smoke-test with reference_solver (must reproduce ~7K mean canonical score). Validates Stage 2 + Stage 3 in isolation.
3. **Phase 3:** Build the minimal agent loop. Validate with Claude at the shim — produces an LLM-driven submission, runs through the full pipeline, leaderboard gets its ceiling reference row.
4. **Phase 4:** Swap shim backend for vLLM client. Run Tier 1 against 3-5 candidate models; confirm the pattern.
5. **Phase 5+ (later):** Tier 2 (LangGraph image, scoped network), Tier 3 (OpenHands SDK), Tier 4 (meta-orchestrator).

### 10. Stack pinned at lab inception

```
core (everywhere):
  python:3.12-slim        # base
  pydantic                # all artifact schemas
  numpy                   # env + solvers

tier 1 image:
  + transitions           # declarative FSM library (declared in prompt)

tier 2 image:
  + langgraph             # state-graph runtime for tier 2-3
  + openai                # vLLM-compatible client
  + tenacity              # LLM-call retries
  + structlog             # events.jsonl

tier 3-4 image:
  + openhands-sdk         # reuse wiki-bench's pin

orchestrator (host):
  pydantic + typer + structlog + bandit + docker (Python SDK)
```

## Consequences

- **Plus**: forge gains a *quantitative*, *verifiable* comprehensiveness scoreboard. Model selection becomes diff-able across throughput and quality axes.
- **Plus**: tier ladder reveals which models can orchestrate (tiers 2-4) vs. just code (tier 1) — directly relevant to forge's wiki-compile production agent.
- **Plus**: extends naturally to other tasks (custom puzzles, RL envs, ARC-AGI) — only the task module changes; harness/sandbox are reusable.
- **Plus**: rl-2048 primitives reused — no env drift between training and eval.
- **Minus**: 4 Docker images to maintain (one per tier). Mitigation: shared base layer; ~30 min/tier extra setup.
- **Minus**: tiers 2-4 are non-deterministic (LLM calls). Mitigation: `temperature=0` + seeded vLLM + N-sample mean.
- **Minus**: scoring 2048 alone may not generalise. Tier 4 may need additional task variety (TBD when we get there).

## Invariants

- A new tier landing in reward-bench ships its own pinned Docker image (`reward-bench/tier{N}/Dockerfile`) with image digest recorded in every artifact's `meta.json`. Submitting code without an immutable image digest is a P3 FAIL.
- Every submission is replay-checked. A submission whose replay score differs by > 5 % (tier 2-4) or > 0 (tier 1) is rejected with verdict=`rejected` — its score does NOT enter the leaderboard.
- The score-computing logic lives inside `/env` (read-only mount). A submission that writes to `/reports/result.json` directly is auto-rejected — only the harness writes there.
- The same vLLM endpoint serving the candidate model also serves the LLM calls inside tier-2-4 submissions. The model is testing its own delegation ability, not delegating to a smarter model.

## Alternatives considered

- **Single Docker image for all tiers.** Rejected because tier 1 needs `--network=none` (closed-world, no LLM calls allowed) but tier 2-4 need network access to vLLM. Different network policies require different runtime configurations; cleanest split is one image per tier.
- **Use `RestrictedPython` instead of Docker.** Rejected — RestrictedPython breaks numpy and most useful libraries; partial sandbox is worse than full Docker.
- **LLM-as-judge for comprehensiveness.** Rejected by architect (this ADR's driver). Verifiable rewards required.
- **Run on real wiki-compile output (no separate task).** Rejected because wiki-compile output isn't directly scoreable without judge or human review — defeats the verifiable-rewards constraint.
- **Use existing rl-2048 lab as the bench.** Rejected — rl-2048 is a *training* lab (Jupyter + GRPO + Unsloth + CUDA). reward-bench is *evaluation*: CPU-only, immutable Docker, per-attempt reproducibility. Different concerns, different Dockerfile, different lifecycle.

## Follow-ups

- Tier 4 framework decision (OpenHands vs. CrewAI) — defer until Tier 3 results land. Possible that OpenHands' meta-mode suffices for the program-synthesis test of tier 4; if not, add CrewAI as a second tier-4 variant.
- Add additional task domains: ARC-AGI puzzles, simple optimisation problems (TSP/job-scheduling), custom multi-step probes. Each task = a new module under `reward-bench/tasks/<task_id>/`.
- Wire reward-bench into the audit predicate set: P32 (proposed) — every model entry in `models.yml` with `bench_tier: A` must have a recent reward-bench score in the leaderboard within N days.
- Extend models.yml schema with `reward_bench_tier_N_score` fields (auto-populated by the harness).
