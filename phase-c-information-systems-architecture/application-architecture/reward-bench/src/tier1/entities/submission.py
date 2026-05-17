"""§7 `Submission` entity — what the per-iter orchestrator returns to main.

`bench :: Env -> BenchConfig -> Submission`

Pure domain type — no IO. Frozen so instances are hashable / immutable
value objects (Senior Haskell AI Engineer stance: immutability over
mutation).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Submission:
    body: str
    score: float
    walltime_sec: float
