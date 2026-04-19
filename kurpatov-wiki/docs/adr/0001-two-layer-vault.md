# ADR 0001 — two-layer vault (raw + wiki)

## Status
Accepted (2026-04-19). Partially amended by
[ADR 0005](0005-split-transcribe-and-push.md): the two layers now live
in two separate git repos (`kurpatov-wiki-raw`, `kurpatov-wiki-wiki`)
rather than as siblings inside one. The on-disk layer split described
here is unchanged.

## Context
The "video → wiki" pipeline is at least three qualitatively different
steps:

1. Audio → text (faster-whisper). Expensive (tens of minutes of audio at a
   time on a GPU) but one-off. The result is objective and has no
   interpretation.
2. Text → summary / notes. Needs an LLM, prompts, possibly multiple
   iterations, possibly multiple styles on the same transcript.
3. Collection of summaries → navigation / cross-references.

The invariant between these steps is drastically different: (1) is
deterministic given a pinned model version, (2) is not, (3) is a
derivative of (2).

If we put everything in one folder with one format, there's an inevitable
temptation to redo step 1 because of changes in step 2. That's wrong — way
too expensive.

## Decision
The vault is split into layers:

```
vault/
├── raw/     ← output of step 1, immutable from downstream's viewpoint
└── wiki/    ← output of steps 2+, freely regeneratable from raw/
```

Rules:

- `raw/` is read-only for downstream layers. Deleting/overwriting is only
  allowed during an explicit migration (e.g. model upgrade).
- `wiki/` can be deleted and regenerated from `raw/` at any time. This
  should be a cheap operation (hours of LLM API or local inference, not
  days of GPU time).

## Consequences
- Plus: a clear boundary between "expensive and irreversible" and "cheap
  and re-computable".
- Plus: different wiki styles (for me, for publishing, thematic cards)
  coexist without re-transcribing.
- Plus: different backup strategies: `raw/` is precious (expensive to
  recompute), `wiki/` can skip backups.
- Minus: two folders instead of one. Negligible overhead.

## Alternatives considered
- A single "everything" layer. Rejected, see Context.
- Three layers (raw / clean / wiki), where "clean" is a normalized text
  without timings. Might appear later, but YAGNI for now — LLMs are fine
  directly on `segments[].text`.
