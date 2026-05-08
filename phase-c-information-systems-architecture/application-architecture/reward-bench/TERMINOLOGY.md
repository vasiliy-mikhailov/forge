# reward-bench terminology

A small glossary used consistently across the lab. Adopt these terms in any new doc, commit message, leaderboard entry, code variable, or chart title. Old occurrences are being migrated.

## Roles

- **Candidate model** — the model under evaluation. Drives the agentic loop, writes `/workspace/submission.py`. The leaderboard ranks candidates. Synonym to avoid: "author model" (less precise — the candidate also reads, runs, debugs).
- **Condenser model** — a cheap helper LLM that summarises older history when the candidate's context grows past `--condenser-trigger-tokens`. Default in the lab: `condenser-llama31-8b` on the RTX 5090 (Qwen 2.5-7B and other small models also work). Borrowed from OpenHands' `LLMSummarizingCondenser`.
- **Reference solver** — non-LLM baselines (`reference_fsm.py`, `claude_fsm.py`). Sit at the top of the leaderboard as fixed reference points, not candidates.

## Run structure

- **Trial** — one independent execution of the ralph (agentic) loop. Identified by a unique random seed. Self-contained: produces a single `submission.py` and zero or more `dev_runner` invocations.
- **Replication** — a set of N trials of *one* candidate at *one* configuration. Reported as a single leaderboard row with `mean ± stdev` over the N trials. The standard publication unit.
- **Sweep** — a matrix of replications across configurations (multiple candidates, or one candidate at multiple `--max-iters` / temperature settings, etc.). Implemented by `bin/sweep_tier1.sh`. A degenerate sweep (1 candidate × N trials) is just a replication; reach for `bin/replicate_tier1.sh` instead.
- **Turn** — one write→test→observe cycle inside a trial, marked `=== turn N ===` in the agent log. Capped by `--max-iters`. Reserve "iteration" for the CLI flag itself.
- **Attempt** — the *whole* 3-stage harness for one trial: Stage 1 (ralph loop) → Stage 2 (canonical 20-game eval) → Stage 3 (replay determinism check). The leaderboard scores **attempts**, but standard practice is to publish replication-level numbers (mean ± stdev across attempts).
- **Game** (or *episode*) — one 2048 game played inside Stage 2/3. Stage 2 plays 20 games with the same submission.

## Hierarchy

```
Sweep
└── Replication (= 1 candidate × N trials)
    └── Attempt (= 1 trial + Stage 2 + Stage 3)
        ├── Stage 1: Trial of ralph loop
        │   └── Turn (write → test → observe)
        ├── Stage 2: 20 Games on held-out seeds
        └── Stage 3: 20-Game replay (determinism check)
```

## CLI ↔ vocabulary mapping

| Flag in `agent_loop.py` | Vocabulary term |
|---|---|
| `--shim`, `--model` | candidate model endpoint |
| `--condenser-shim`, `--condenser-model` | condenser model endpoint |
| `--seed N` | trial identifier |
| `--max-iters N` | per-trial **turn** cap |
| `--max-no-improve N` | plateau-stop after N non-improving dev_runs |
| `--finish-floor N` | reject `finish` if best dev MEAN < N |
| `--temperature` | candidate sampling temperature |

## Examples

> "We report the **replication** of Qwen 3.6-AWQ-INT4: 10 **trials**, each capped at 200 **turns**, condensed by Llama-3.1-8B-NVFP4. Mean Stage 2 = 5 320 ± 1 840."

> "The May-08 **sweep** covered 5 candidates × 10 trials each = 50 attempts; the worst replication averaged 1 200 ± 600, the best 8 100 ± 1 100."

> "Within trial 7 the candidate ran 134 **turns** before voluntarily emitting `finish`; the condenser fired twice (after turn 38 and turn 91)."
