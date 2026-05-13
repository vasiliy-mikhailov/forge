"""GameResult: per-game result entity from SPEC.md.

See src-spec/tier1/entities/game_result/src_spec_game_result.md."""
from dataclasses import dataclass
from typing import Literal


FinalState = Literal[
    'won', 'lost', 'max_moves',
    'stagnated',
    'walltime_exceeded',
    'solver_error', 'invalid_action',
]


@dataclass(frozen=True)
class GameResult:
    """One game played by a submission. Mirrors SPEC.md pydantic schema."""

    seed: int
    score: int
    max_tile: int
    moves: int
    final_state: FinalState
    walltime_sec: float
