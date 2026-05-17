"""§7 `Env` entity — the bench environment value object.

`bench :: Env -> BenchConfig -> Submission`
`score :: Env -> Submission -> Score`
`orchestrate :: Env -> BenchConfig -> [Submission]`

Frozen so two orchestrators in a dominance comparison run against
the same Env without mutation drift.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ports.canonical_scorer import CanonicalScorerPort


@dataclass(frozen=True)
class Env:
    tasks_dir: Path
    canonical_scorer: CanonicalScorerPort
