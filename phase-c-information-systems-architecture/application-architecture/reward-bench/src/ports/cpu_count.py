"""CpuCountPort."""
from __future__ import annotations

from typing import Protocol


class CpuCountPort(Protocol):
    """Returns the number of CPU cores available to this process."""

    def cpu_count(self) -> int: ...
