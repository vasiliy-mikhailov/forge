"""Cycle 105 / ADR 0006 Layer 2: CpuCountPort.

Use-case modules can't import `os` (clean-arch test forbids it).
Anything that needs to know how many CPU cores the host has must
get it via this port. Tests inject a fixed-count fake.
"""
from __future__ import annotations

from typing import Protocol


class CpuCountPort(Protocol):
    """Returns the number of CPU cores available to this process."""

    def cpu_count(self) -> int: ...
