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
