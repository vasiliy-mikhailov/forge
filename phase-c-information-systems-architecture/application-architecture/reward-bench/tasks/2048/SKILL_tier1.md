# 2048 — Tier 1 — Erlang Solver

## Goal

Write an Erlang module named `submission` that exports `move/1`.
The function takes a 4×4 board (a list of 4 lists of 4 non-negative
integers; `0` = empty, tiles are powers of 2) and returns one of the
atoms `w`, `a`, `s`, `d` — up, left, down, right respectively.

The harness compiles your module in-VM, plays 20 games on canonical
held-out seeds, and reports the mean score.

## Contract

```erlang
-module(submission).
-export([move/1]).

-spec move(Board :: [[non_neg_integer()]]) -> w | a | s | d.
move(_Board) ->
    w.
```

## What we score

- **20 games** on canonical seeds (different from the dev seeds the
  harness uses for in-loop feedback).
- **Mean game score** is the bench result.
- Per-game wallclock cap: ~5 seconds. Max moves per game: 10000.
- Crashes (exceptions, invalid actions, undefined modules) yield
  score 0 for that game; the bench continues with the next seed.

## What's allowed

- Any function from the Erlang/OTP standard library, callable
  inside `move/1`.
- `move/1` must be a pure function. No `spawn`, no `process_flag`,
  no `file:`, no `gen_tcp:`. The solver runs inside a sandboxed
  Erlang process and the BEAM blocks IO patterns the harness
  doesn't whitelist.

## FSM-style strategies

Erlang's pattern matching makes FSM-shaped solvers natural without
a library. Classify the board, delegate to a per-state heuristic:

```erlang
-module(submission).
-export([move/1]).

move(Board) ->
    case classify(Board) of
        building   -> heuristic_corner_pack(Board);
        endgame    -> heuristic_merge_highest(Board);
        recovering -> heuristic_safe_slide(Board)
    end.

classify(_Board) -> building.
heuristic_corner_pack(_) -> d.
heuristic_merge_highest(_) -> s.
heuristic_safe_slide(_) -> a.
```

## Dev iteration

The harness runs your code after each emission against **5 dev
seeds** and feeds back per-game scores + mean as the next
conversation turn. Iterate until satisfied; the **LAST** fenced
```` ```erlang``` ```` block in your conversation is your final
submission.
