# 2048 — Tier 1 — Static FSM solver

## Goal

Write a Python class `Solver` that plays 2048 to maximize game score. Your solver must be a **state machine** (FSM) — declared explicitly with the `transitions` library — not just a heuristic function.

Save your final answer to `/workspace/submission.py`. The harness will then run it on **canonical held-out seeds** (different from the dev seeds you can test against here) for 20 games and report the mean score.

## What "FSM" means here

You must declare named **states** (e.g. `building`, `endgame`) and explicit **transitions** between them, using the `transitions.Machine` class. Each state has its own move policy (a method).

Minimal correct skeleton (cycle 99b — the library expects each transition entry to be a `dict` or a `list`, NOT a tuple):

```python
from transitions import Machine

class Solver:
    states = ['building', 'endgame']
    transitions = [
        {'trigger': 'advance', 'source': 'building', 'dest': 'endgame'},
        {'trigger': 'retreat', 'source': 'endgame',  'dest': 'building'},
        # Or equivalently:  ['advance', 'building', 'endgame']
    ]
    def __init__(self):
        self.machine = Machine(
            model=self,
            states=self.states,
            transitions=self.transitions,
            initial='building',
        )
    def move(self, board):
        # delegate to the per-state policy method
        return getattr(self, f'_move_{self.state}')(board)
    def _move_building(self, board): return 'W'
    def _move_endgame(self, board):  return 'A'
```

Common wrong form (causes `TypeError: argument after ** must be a mapping`):

```python
transitions = [
    ('advance', 'building', 'endgame'),   # tuple — library rejects
]
```

This is closed-world: your `Solver` runs in a sandbox with **no LLM access during play**. Every decision must be encoded in your Python.

## API contract

```python
class Solver:
    def __init__(self):
        ...
    def move(self, board: list[list[int]]) -> str:
        # Return one of 'W', 'A', 'S', 'D'.
        ...
```

Action mapping:

| Action | Direction |
|---|---|
| `W` | up |
| `A` | left |
| `S` | down |
| `D` | right |

The board is a 4×4 nested list of integers. Empty cells are 0; tiles are powers of 2. Two equal-value adjacent tiles merge when slid in their direction.

If your `move()` returns an action that wouldn't change the board, the harness substitutes the first legal action (so you don't have to handle this — but it costs you a move that could've been a real merge).

## Allowed imports (tier-1 whitelist)

```
__future__, ast, collections, copy, dataclasses, enum, functools, heapq,
itertools, math, operator, random, re, statistics, string, typing
numpy
transitions          # the FSM library — your solver MUST use this
env_2048             # provided in /env (read-only) — only if you want to inspect
```

Anything else (`os`, `subprocess`, `socket`, `pickle`, `eval`, `exec`, `__import__`, etc.) is rejected by the static AST scan and your submission gets verdict=`rejected`. **No timing-based randomness either** (`time.time()`, `os.urandom`) — those defeat the replay-determinism check. Use `random.Random(seed)` if you need any randomness.

## Iterating (turns within a trial)

You are inside a single **trial** of the agentic loop. Each cycle below is one **turn**; the harness caps your turns via `--max-iters`. Suggested workflow:

1. **Read** `/env/env_2048.py` to understand the env (board shape, action API, state machine).
2. **Sketch** a Solver in `/workspace/submission.py`.
3. **Test** with: `python3 /tasks/2048/dev_runner.py /workspace/submission.py`
   This plays 5 games on dev seeds and prints scores. Fast feedback loop (~5-30s).
4. **Refine**: tune your states, transitions, per-state policies. Re-test.
5. **Finish** when your dev mean score plateaus or your turn budget is up.

Vocabulary used here is defined in [TERMINOLOGY.md](../../TERMINOLOGY.md). Quick map: you are the **candidate model**, this loop is one **trial**, each cycle is one **turn**, and a series of trials becomes a **replication** that goes on the leaderboard.

The dev runner uses seeds 1-5; the canonical eval uses different seeds (1000-1019). Don't bother memorizing seed-specific patterns.

## What we score

After you call `finish`, the harness:

1. Runs static anti-cheat AST + bandit on your submission.
2. If verdict is `rejected`, your run is marked failed and gets score 0.
3. Otherwise, runs your submission in a fresh sealed Docker container (`--network=none`) on canonical seeds 1000-1019 (20 games), target=2048, max_moves=10000.
4. Replays in another fresh container with the same seeds. **Replay scores must match exactly** — any non-determinism (timing-based randomness, file state) = run rejected.

The score we report is the **mean game score over the 20 canonical games**.

## Per-game stagnation detector

Stage 2 does NOT have a fixed walltime budget. Instead, **each game runs as long as it's making progress**, where progress = score increasing OR max-tile increasing. If neither has changed for **60 seconds** of wall time, the game ends with `final_state="stagnated"` and whatever score was accumulated counts.

- The stagnation window is per-game, not per-attempt — fast solvers play 20 games quickly; slow solvers can take longer if each game is genuinely advancing.
- A solver stuck in a tight loop emitting illegal actions, or trapped against the corner with no legal merges, will trip the detector within 60 s.
- An outer `REWARD_BENCH_HARD_WALL_SEC` runaway cap is available but disabled by default.

Practical implication for tier 1: the reference FSM finishes in ~6 s total over 20 games and the Claude reference in ~108 s, so neither comes close to triggering. The detector mostly matters for tier 2-4 where each move is an LLM call, so 60 s ≈ 30-60 moves before abort if no merges are happening.

If you see `stagnated` games in your dev runs, your solver is making no merges in some configurations — fix the policy or break the bad pattern.

## Reference scores

For calibration:

| Solver | Mean score | Max-tile reached |
|---|---|---|
| Random moves | ~1 000 | 128 |
| Hand-written FSM (the harness author's reference) | ~7 000 | 2 048 (occasionally) |
| Textbook expectimax 3-ply | ~40 000–80 000 | 2 048+ routinely |

You're competing against the hand-written FSM. Beating it = the model is doing real work, not just pattern-matching template solvers.

## Anti-patterns (will be detected and rejected)

- `import os` / `subprocess` / `socket` — sandbox-escape
- `eval(...)`, `exec(...)`, `compile(...)` — dynamic code
- `__import__("x")` — dynamic import
- Reading `/proc/...` or `/etc/...` — info exfil
- `time.time()` for any logic — non-determinism
- Writing files outside `/workspace/` — info exfil
- Writing directly to `/reports/result.json` — score forgery (the harness owns this file)

## Submission checklist

Before calling `finish`:

- [ ] `/workspace/submission.py` exists and defines `class Solver`.
- [ ] `Solver.move(board)` returns one of `W`, `A`, `S`, `D`.
- [ ] Solver uses `transitions.Machine` to declare states + transitions.
- [ ] You ran the dev_runner at least once and got non-error output.
- [ ] No banned imports / no timing-randomness / no I/O outside `/workspace/`.
