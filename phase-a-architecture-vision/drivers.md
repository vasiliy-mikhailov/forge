# Drivers

Per [ADR 0014](../phase-preliminary/adr/0014-archimate-across-all-layers.md),
every Driver in this file is connected to its Goal via the
ArchiMate *Influence* relationship (spec §5.2.3) — annotated
inline as `→ influences <Goal>`.

- Time spent consuming information from Russian psychology
  lectures (Kurpatov: ~60-90 min each, ~200 in catalog).
  → influences **TTS** (Theoretical Time Saved).
- Time spent writing/optimizing programs in domains where RL
  with verifiable rewards (RLVR) can do the slog automatically.
  → influences **TTS**, **PTS** (Practical Time Saved).
- Architect-velocity: every minute the architect spends
  recovering GPUs or rerunning failed pilots is a minute not
  spent on the real work.
  → influences **Architect-velocity** (Phase A).

- Token-count bloat in operational md (low-information-density
  prose, restated context, orphan headers, decorative repetition,
  the file's own H1 re-stated in the body) inflates every LLM
  read of that file, slowing the agent and diluting the signal
  the agent is supposed to act on.
  Carve-out: *downloaded standards* — ArchiMate spec, TOGAF
  reference, third-party PDFs / transcripts under research-corpus
  paths (anything under `**/standards/**`, `**/vendor/**`,
  `**/external/**`, or any md whose first non-blank line is the
  HTML comment `<!-- standard: external -->`). These are
  reference material, not forge-authored operational text; they
  are not under forge's editorial control and their token cost is
  amortised across reads.
  → influences **Architect-velocity** (Phase A) and **TTS** (an
  agent that has to load more tokens per task takes longer to
  produce the same act).


## Motivation chain

Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: meta — this file IS the Drivers catalog. P18
  walks each Driver → Goal arrow.
- **Goal**: TTS + Architect-velocity (Phase A).
- **Outcome**: every Phase B / D requirement (R-NN) traces
  to a Driver via P15.
- **Capability realised**: Architecture knowledge management.
- **Function**: Catalogue-Phase-A-Drivers.
- **Element**: this file.
