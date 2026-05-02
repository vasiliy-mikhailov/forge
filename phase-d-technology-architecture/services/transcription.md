# Service: Audio → text transcription

- **Component:** faster-whisper.
- **Lab:** [`wiki-ingest/`](../../phase-c-information-systems-architecture/application-architecture/wiki-ingest/).

## Quality dimensions and trajectories

- **Russian-WER** on a held-out audit set — L1: ~200 Курпатов
  lectures transcribed end-to-end. Output is the `raw.json`
  whisper-segment shape consumed downstream.
  L2: stable; not on the active trajectory.


## Motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: audio-to-text transcription is the entry
  point of the wiki pipeline.
- **Goal**: TTS (raw.json must exist before any compaction).
- **Outcome**: wiki-ingest faster-whisper transcribes audio
  + pushes raw.json per ADR 0005.
- **Measurement source**: lab-tests: WI (wiki-ingest smoke + pusher container health)
- **Capability realised**: Service operation + Product delivery.
- **Function**: Transcribe-audio-to-raw-json.
- **Element**: this file.
