# reward-bench leaderboard — Tier 1 (2048)

Per [ADR 0029](../../../phase-preliminary/adr/0029-reward-bench.md). Vocabulary: [TERMINOLOGY.md](TERMINOLOGY.md). Each row is one **attempt** (a **trial** of the ralph loop + Stage 2 + Stage 3) by a **candidate model**; May-08+ rows are **replications** (mean ± stdev over N=10 trials). Stage-2 scores: mean over 20 canonical **games** on seeds 1000-1019, target=2048, max_moves=10000, per-game stagnation budget (60s — see SPEC). Sandbox: `reward-bench-tier1:0.3`, `--network=none`, deterministic.

## Tier 1 — static FSM

| Submission | Candidate / notes | Mean | Median | Max | Max-tile reached | Won (out of 20) | Walltime |
|---|---|---:|---:|---:|---:|---:|---:|
| Random | (floor) | ~1 000 | ~1 000 | ~1 500 | 128 | 0 | <1 s |
| `reference_fsm.py` | hand-written FSM (corner-anchor + 1-ply expectimax) | 7 211 | 6 192 | 14 436 | 1 024 | 0 | 6 s |
| **candidate-tier1: qwen3.6-27b-awq-int4** | **Qwen 3.6-27B (AWQ-INT4)** — agent_loop, 35 turns, dev MEAN=12 165 (2 wins/5 dev seeds, max-tile 2048). Snake-anchor + state-machine FSM. ⭐ first model to beat Claude reference. | **10 884** | **8 144** | **21 208** | **2 048** | **4** | 6 s |
| `claude_fsm.py` | **Claude (harness ceiling reference)** — 2-ply expectimax + snake heuristic | 8 632 | 7 012 | 20 440 | 2 048 | 2 | 108 s |
| candidate-tier1: qwen3.6-27b-nvfp4 | Qwen 3.6-27B (NVFP4) — agent_loop, 25 turns, 589 s Stage-1 walltime | 4 401 | 4 220 | 7 316 | 512 | 0 | 0.4 s |
| candidate-tier1: qwen3-32b-fp8 | Qwen 3-32B (FP8) — agent_loop, 9 turns + voluntary `finish`, 77 s Stage-1 walltime | 2 585 | 2 544 | 4 344 | 256 | 0 | 0.2 s |
| candidate-tier1: qwen3.5-27b-nvfp4 | Qwen 3.5-27B (NVFP4-A16, kaitchup pack) — agent_loop, 61 turns + voluntary `finish`, dev MEAN=9 331 max-tile=1024 | 6 847 | 6 436 | 14 364 | 1 024 | 0 | 0.1 s |
| candidate-tier1: nemotron-super-49b-v1.5-nvfp4 | Llama-3.3-Nemotron-Super 49B (NVFP4) — **skipped**: reasoning model burns 5+ min of `<think>` per turn at 35 tok/s decode; Stage 1 didn't produce its first reply within reasonable bounds. Tier 1 harness assumes non-reasoning authors. | — | — | — | — | — | — |
| candidate-tier1: gemma-4-31b-nvfp4 | Gemma 4 31B IT (NVFP4) — agent_loop, 10 turns + voluntary `finish` at 121 s, dev MEAN=2 054 max-tile=256 | 1 303 | 1 072 | 2 680 | 256 | 0 | 0.1 s |
| candidate-tier1: llama-3.1-8b-nvfp4 | Llama 3.1 8B Instruct (NVFP4) — **rejected**: at registry's 32K context, agent_loop overflows by turn 3 (rolling history >20K, +12K output reservation = 32 769 vs 32 768 max). Bumped to yarn factor 8 (max 64K), but at 64K extension the model degenerates into incoherent output (repeated single tokens). 8B is too small and yarn-extended too far for this harness. | — | — | — | — | — | — |
| candidate-tier1: qwen2.5-72b-nvfp4 | Qwen 2.5-72B Instruct (NVFP4, enfuse) — agent_loop, 8 turns + voluntary `finish` at 221 s, dev MEAN=2 574 max-tile=256 | 2 921 | 2 946 | 5 128 | 512 | 0 | 0.2 s |
| candidate-tier1: llama-3.3-70b-nvfp4 | Llama 3.3 70B Instruct (NVFP4) — **rejected**: in 1 turn (17 s), model emitted multiple stacked fenced tool blocks (view + write_file + bash + finish) and copied the placeholder text `... your full file, raw, no JSON escaping ...` from the system-prompt example into submission.py, then called `finish`. SyntaxError at parse — submission unloadable. Pure instruction-following failure. | — | — | — | — | — | — |
| candidate-tier1: gpt-oss-20b | OpenAI gpt-oss-20b (native MXFP4, 32-expert MoE, 4 active = ~3.6B effective) — agent_loop, ~54 turns to write a working FSM, then stuck in reasoning loop. Required (1) bypass docker-compose to drop `--tool-call-parser`, (2) patch agent_loop to coalesce `content=None` and concat `reasoning + content` so harmony channel output reaches the parser. Dev MEAN=3 241 max-tile=512 | 2 990 | 2 998 | 6 812 | 512 | 0 | 0.1 s |
| candidate-tier1: gpt-oss-120b | OpenAI gpt-oss-120b (native MXFP4, 128-expert MoE, 4 active) — **smart-harness re-run** (best-checkpoint, plateau, finish-floor; max-iters 30): 30 turns, peak dev MEAN=4 866 at turn 25 (was 3 328 in original 20-turn run). Best-snapshot restored to submission.py for Stage 2. | **4 683** | 5 360 | 6 652 | 512 | 0 | 0.2 s |
| candidate-tier1: devstral-small-2-24b | Devstral-Small 2-24B Instruct (NVFP4, Firworks pack) — **rejected**: 38 turns, every dev_run scored MEAN=0 max-tile=4. Model can't escape the `transitions` library API misuse loop — keeps writing `self.machine.state` instead of `self.state`, never recovers despite the dev_runner's clear error message. Same failure mode as the May-05 attempt. Devstral coding-tuning doesn't translate to library API recall on this task. | — | — | — | — | — | — |
| candidate-tier1: nemotron-super-49b-v1.5-nvfp4 | Llama-3.3-Nemotron-Super 49B v1.5 (NVFP4) — **skipped (retry)**: same outcome as the May-05 attempt — reasoning model burns >5 min of `<think>` per turn at 35 tok/s decode, never produces a first reply. Tier 1 harness assumes non-reasoning authors. (Note: harmony-channel handling now in agent_loop didn't help — Nemotron uses `<think>` tags, not OpenAI's harmony format.) | — | — | — | — | — | — |
| candidate-tier1: devstral-2-123b-nvfp4 | Devstral 2 123B Instruct (NVFP4, BrainForge) — **rejected**: 70 GB model required `--max-model-len 16384` (FlashInfer workspace overflow at 32K + Mistral-Large arch needs `--attention-backend TRITON_ATTN`). At 16K context, agent_loop overflows (rolling history > 4K + 12K output reservation = 16,385 > 16,384). Wrote 8KB submission but it includes the literal `---` body separator from the write_file fenced-block protocol, causing SyntaxError on import. | — | — | — | — | — | — |
| candidate-tier1: nemotron-3-super-120b-nvfp4 | NVIDIA Nemotron 3 Super 120B-A12B (NVFP4, MoE, ~12B active) — agent_loop, 14 turns + voluntary `finish` at 128 s. Used patched agent_loop with `===FILE_BODY===` separator + 32K context (TRITON_ATTN, max-num-seqs=64 for Mamba cache). Dev MEAN=5 674 max-tile=512. | 4 457 | 4 276 | 7 496 | 512 | 0 | 0.1 s |
| (tbd) | other candidate models via agent_loop → Stage 2 | — | — | — | — | — | — |

## What the numbers mean

- **Mean score** is the headline metric — Tier 1 ranks models by this.
- **Max-tile reached** tells us whether the strategy can sustain the snake/corner pattern into late game.
- **Won** = reached 2048 tile (game terminates as `won` state).
- **Walltime** is the canonical-eval wall time; correlates with strategy depth (1-ply vs 2-ply expectimax). Not part of the score.

## Reference scores beyond reward-bench (just for orientation)

| Solver | Mean score | Notes |
|---|---|---|
| Textbook expectimax 3-ply (literature) | ~40 000-80 000 | Way more compute per move; not in our bench |
| Well-tuned MCTS / RL | 100 000+ | Definitely not in our bench |

**Claude's 8 632 ceiling sits well below textbook 3-ply expectimax** — intentional. Tier 1 measures whether models can produce a reasonable static FSM, not state-of-the-art search.

## Candidates queued

The 12 models from the throughput sweep + Devstral, all expected to attempt Tier 1:

```
qwen25-7b           Mistral-Nemo-12B           qwen25-14b
mistral-small-3.2-24b   devstral-small-2-24b   qwen36-27b
gemma3-27b          qwen3-32b                  gemma4-31b
llama33-70b         qwen25-72b                 (devstral-2-123b: tbd)
```

Each goes through:

1. Stage 1 — OpenHands ralph loop with the candidate model writing/iterating on submission.py against dev seeds 1-5.
2. Stage 2 — canonical 20-game eval at seeds 1000-1019.
3. Stage 3 — replay determinism check (Tier 1: must match Stage 2 exactly).

Expected outcome: most candidates score below the Claude ceiling (~9 000) but above random (~1 000). The interesting differential is between architecture families and parameter sizes within the candidate band.

## Methodology notes

- **Stage 2 is closed-world.** No LLM calls during play. Submissions that import `langgraph`/`openai` get rejected by the AST scan (those are Tier 2+ libraries).
- **Replay determinism** is exact-match for Tier 1. Any submission whose Stage 3 score differs from Stage 2 is `verdict: rejected` and doesn't enter the leaderboard.
- **Sandbox image is digest-pinned.** `meta.json` records `image_digest`; given that + submission sha256 + seed range, anyone can reproduce.
- **Anti-cheat:** AST allow-list + bandit. See `bin/anti_cheat.py`.
- **Calibration runs are reproducible:** `make smoke-tier1` re-runs the reference FSM and must output mean_score=7 211.2, median=6 192. Drift in this number = harness regression.
