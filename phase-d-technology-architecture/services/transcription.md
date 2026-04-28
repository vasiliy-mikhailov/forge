# Service: Audio → text transcription

- **Component:** faster-whisper.
- **Lab:** [`wiki-ingest/`](../../phase-c-information-systems-architecture/application-architecture/wiki-ingest/).

## Quality dimensions and trajectories

- **Russian-WER** on a held-out audit set — L1: ~200 Курпатов
  lectures transcribed end-to-end. Output is the `raw.json`
  whisper-segment shape consumed downstream.
  L2: stable; not on the active trajectory.
