# `src/tier1/entities/game_result.py`
`GameResult` is a frozen dataclass — the per-game record produced when
a submission plays one game. Mirrors the pydantic schema declared in
[`SPEC.md`](../../../../SPEC.md#schemas-pydantic-v2).
## Fields
| Field | Type | Meaning |
| -------------- | ------------ | ------------------------------------------------ |
| `seed` | `int` | RNG seed the game was played with. |
| `score` | `int` | Final game score (must be ≥ 0 per SPEC.md). |
| `max_tile` | `int` | Highest tile reached (must be ≥ 2 per SPEC.md). |
| `moves` | `int` | Total moves played (must be ≥ 0 per SPEC.md). |
| `final_state` | `FinalState` | How the game ended; one of 7 string literals. |
| `walltime_sec` | `float` | Wall-clock seconds the game consumed. |
## `FinalState`
A `Literal` over 7 strings, taken verbatim from `SPEC.md`:
- `won` — the game met a win condition.
- `lost` — board filled, no legal moves.
- `max_moves` — fixed move budget exhausted.
- `stagnated` — `REWARD_BENCH_STAGNATION_SEC` elapsed with no score
 or max-tile progress.
- `walltime_exceeded` — outer hard-wall cap fired.
- `solver_error` — the submission raised an exception.
- `invalid_action` — submission returned a non-WASD action.
## Properties
- Frozen. No mutation after construction.
- No validation in this layer. SPEC.md's pydantic-side constraints
 (`score >= 0`, etc.) are enforced at the adapter boundary, not in
 the entity itself.
- No methods. Pure data.
## Where it sits
`tier1/entities/` because a game is tier-1's atomic scoring unit; an
`AttemptResult` aggregates many `GameResult` values.
