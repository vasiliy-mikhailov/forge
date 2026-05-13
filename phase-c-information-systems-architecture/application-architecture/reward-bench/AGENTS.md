# reward-bench — operating environment for the agent

Per [ADR 0029](../../../phase-preliminary/adr/0029-reward-bench.md) + [SPEC.md](SPEC.md).

## What this lab is

A Docker-sandboxed evaluator that runs a candidate LLM through a 4-tier ladder of agentic puzzle-solving tasks. Each tier asks the model to write (or assemble) an FSM that maximises a verifiable quantitative reward. Tier 1 is closed-world Python FSM. Tiers 2-4 add increasing meta-orchestration. First task: 2048.

This lab is the *comprehensiveness scoreboard*. Throughput is measured separately by `bench-fp8-16k.sh` / `bench-nvfp4-16k.sh`. reward-bench answers: «given that a model is fast enough, can it actually orchestrate to solve a task?»

## Mode mutex

CPU-only — co-runs with whichever lab/mode is providing inference. Required prerequisite: `${INFERENCE_DOMAIN}` is reachable from the proxy-net network (i.e., `wiki-compiler` or `inference` mode is up serving the candidate model).

## Two-stage harness (Tier 1; same shape for Tier 2-4 with different image)

```
Stage 1 — AUTHOR (with ralph loop)
  Sandbox A: agent has tools (file_editor, bash, view, finish).
  Agent reads /tasks/2048/SKILL.md, iteratively writes /workspace/submission.py,
  uses bash to run /tasks/2048/dev_runner.py for fast feedback on dev seeds 1..5.
  Until 'finish' or budget (N iterations / M wall-time).

Stage 2 — CANONICAL EVAL
  Sandbox B (Dockerfile.tier1, --network=none).
  Plays 20 games at canonical held-out seeds 1000..1019.
  Writes /reports/result.json + /reports/events.jsonl.

Stage 3 — REPLAY
  Same as Stage 2 in fresh container. Tier 1: scores must match exactly.
```

## Anti-cheat

- AST static walk + bandit on `/workspace/submission.py` (host-side, before Stage 2).
- `--network=none` (tier 1) means no exfil even if the AST scan misses something.
- Replay determinism — Stage 2 and Stage 3 must produce identical scores. Mismatch = `verdict: rejected`.

## Per-attempt artifact layout

`/mnt/steam/forge/labs/reward-bench/experiments/<run_id>/`:

```
meta.json               # model_id, task_id, tier, image_digest, started_at
prompt.txt              # what the agent received
raw_response.txt        # full agent response (or last response)
submission.py           # the candidate's final solver
submission.sha256       # for replay verification
cheat-check.json        # AST + bandit verdict
result.json             # {games, mean_score, median, max_max_tile}
result-replay.json      # second-run result (verifies determinism)
events.jsonl            # per-step game trace
sandbox.log             # container stdout/stderr
done                    # touch-marker; presence = run finalised
```

## Make targets

```
make build-tier1                                  # build Stage-2 sandbox image
make smoke-tier1                                  # smoke test with reference FSM
make shim ROOT=<dir> PORT=<port>                  # start Claude-fixture shim
make claude-fixture-tier1 RUN_ID=<x> SHIM=<url>   # run agent loop against shim
make attempt MODEL=<id> TIER=<n> TASK=<id>        # full attempt against vLLM
make clean DAYS=<n>                               # GC old artifacts
```

## File layout

```
reward-bench/
  SPEC.md                          # what this lab is
  AGENTS.md                        # this file (operating env for agents)
  Makefile                         # make targets
  Dockerfile.tier1                 # Stage 2 sandbox image
  bin/
    claude_shim.py                 # OpenAI-compat HTTP shim → file-handoff to Claude
    anti_cheat.py                  # AST + bandit static checks
    orchestrator.py                # ties Stage 1 + 2 + 3 together (TBD)
  tasks/
    2048/
      env.py                       # GameBoard (lifted from rl-2048)
      runner_canonical.py          # Stage 2 + 3 runner (in-container)
      dev_runner.py                # Stage 1 fast-feedback for ralph loop
      SKILL_tier1.md               # tier 1 prompt
      baselines/
        reference_fsm.py           # hand-written FSM; calibration ceiling
```

## How to add a new task

1. Create `tasks/<task_id>/`.
2. Drop in: `env.py`, `runner_canonical.py`, `dev_runner.py`, `SKILL_tier{N}.md`.
3. Optional: `baselines/reference_fsm.py` for calibration.
4. Extend `bin/orchestrator.py`'s task registry.
5. Bump SPEC.md's task list.

## How to add a new tier

1. Add `Dockerfile.tier{N}` extending the previous tier's image.
2. Add `tasks/<task>/SKILL_tier{N}.md` with constraints + allowed-imports list.
3. Extend `bin/anti_cheat.py`'s per-tier whitelist.
4. Wire iptables egress for the new sandbox if open-world.
5. Land an ADR amendment.

## Cross-references

- [SPEC.md](SPEC.md) — formal lab spec
- [ADR 0029 — reward-bench](../../../phase-preliminary/adr/0029-reward-bench.md)
- [ADR 0015 — verifiable agent rewards](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
- [wiki-bench/SPEC](../wiki-bench/SPEC.md) — sibling lab, source of the Docker pattern
- [rl-2048/notebooks/2048_gpt_oss_20b.ipynb](../rl-2048/notebooks/2048_gpt_oss_20b.ipynb) — source of the GameBoard env

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: ADR 0029 + architect call (2026-05-04) — comprehensiveness needs verifiable signal beyond throughput.
- **Goal**: [Quality](../../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95).
- **Outcome**: this AGENTS.md + SPEC.md + Dockerfile.tier1 + 2048 task module + harness scripts.
- **Measurement source**: lab-tests: RB (smoke-tier1 + AGENTS Phase A-H integrity).
- **Contribution**: defines the operator's interface to the new lab.
- **Capability realised**: [Architecture knowledge management](../../../phase-b-business-architecture/capabilities/forge-level.md).
- **Function**: Document-reward-bench-operator-interface.
- **Element**: this file.

---

## Methodology

The full CATS (Clean Architecture Test Specs) methodology — every cycle's eleven steps, the discipline rules, the spec hierarchy, the structural-test contract — lives at the forge root in [`AGENTS.md`](../../../AGENTS.md) (canonical source at [`phase-preliminary/cats.md`](../../../phase-preliminary/cats.md)). Read it before opening an editor for this lab. The reward-bench discipline is exactly CATS — no lab-specific deviations beyond the module names called out in this file.
