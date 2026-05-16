"""Cycle 105 / ADR 0006 Layer 2: MultiprocessingCpuCount adapter.

Production binding for CpuCountPort. Uses multiprocessing.cpu_count
(stdlib, no `os` import in caller).
"""
from __future__ import annotations

from src.ports.cpu_count import CpuCountPort


class MultiprocessingCpuCount(CpuCountPort):
    def cpu_count(self) -> int:
        import multiprocessing
        try:
            return int(multiprocessing.cpu_count())
        except NotImplementedError:
            return 1


class FixedCpuCount(CpuCountPort):
    """Test fixture: returns whatever the caller asked for."""

    def __init__(self, n: int):
        self._n = int(n)

    def cpu_count(self) -> int:
        return self._n
