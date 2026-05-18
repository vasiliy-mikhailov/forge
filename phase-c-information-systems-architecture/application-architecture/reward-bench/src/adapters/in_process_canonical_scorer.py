"""InProcessCanonicalScorer adapter.

Wraps `score_submission` as a `CanonicalScorerPort`. Exists for
offline benchmarking when Docker isn't available; production uses
`DockerCanonicalScorer`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.ports.canonical_scorer import CanonicalScorerPort
from src.tier1.entities.attempt_result import AttemptResult


class InProcessCanonicalScorer(CanonicalScorerPort):
    """Wraps `score_submission` as a `CanonicalScorerPort`.

    Loads the submission module, instantiates `Solver`, plays the
    seeds via the daemon-thread harness, returns an `AttemptResult`.
    Isolation is best-effort (Python thread, not OS process).
    """

    def __init__(self, env=None):
        # Default env: tier-1's GameBoard2048Adapter. Tests can inject
        # a synthetic env.
        if env is None:
            from src.tier1.adapters.game_board_2048 import GameBoard2048Adapter
            env = GameBoard2048Adapter()
        self._env = env

    def score_body(
        self,
        body: str,
        seeds: Iterable[int],
        *,
        hard_wall_sec: float = 0.0,
    ) -> AttemptResult:
        from src.tier1.use_cases import score_submission as _ss
        ns: dict = {}
        exec(compile(body, '<submission>', 'exec'), ns)
        solver_cls = ns['Solver']
        return _ss.score_submission(
            solver_cls, list(seeds), self._env,
            hard_wall_sec=hard_wall_sec,
        )

