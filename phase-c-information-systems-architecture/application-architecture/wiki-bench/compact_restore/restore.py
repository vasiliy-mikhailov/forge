"""K2-R1 restore() L1 — identity.

L1 Air-strip drops ONLY information-free Air patterns. There is
nothing to reconstruct from pointers (L2) or concept-graph deltas
(L3) yet, so restore_l1 is a structural identity that confirms
the input came through L1 (compact_metadata.layer == 'L1') and
returns it.

This is on-purpose. The K2 spec lists L1's bwd_recall = fwd_recall
because L1 is lossless: any idea preserved through compact_l1 is,
by definition, recoverable from the compact form (it's still
there in plain prose).

L2 and L3 restore() will follow pointers and concept links — the
implementation lands when L2/L3 compact() lands.
"""
from __future__ import annotations


def restore_l1(compact: dict) -> dict:
    """Identity restore. Validates layer = L1; returns the input."""
    meta = compact.get('compact_metadata', {})
    if meta.get('layer') != 'L1':
        raise ValueError(
            f'restore_l1 expects layer=L1, got {meta.get("layer")!r}; '
            f'use restore_l2 or restore_l3 for higher layers.'
        )
    return compact
