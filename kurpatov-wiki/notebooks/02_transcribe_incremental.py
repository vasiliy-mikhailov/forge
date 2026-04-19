"""
Incremental transcription for the Kurpatov-wiki vault.

Recursively scans /workspace/videos/, compares against the list of existing
transcripts under /workspace/vault/raw/<...>/<video_stem>/raw.json, and only
processes the missing ones via faster-whisper large-v3 on cuda:0.

Output format: a single raw.json file. Fields:
  info.language               — language detected by whisper
  info.duration               — audio duration
  info.language_probability   — language detection confidence
  info.source_path            — source mp4
  info.model                  — whisper model name
  info.compute_type           — precision (float16 / bfloat16 / ...)
  info.beam_size              — beam size during decoding
  info.transcribed_at         — ISO-8601 UTC
  info.diarized               — bool; currently always False, pyannote will
                                later update segments and flip this flag
  segments[].id               — sequential number
  segments[].start / .end     — seconds from the start of audio
  segments[].text             — recognized segment text
  segments[].speaker          — null (placeholder for diarization)
  segments[].words[]          — word-level timestamps and prob

Two tqdm progress bars:
  - outer — total audio duration across the whole queue
  - inner — progress through the current file

Atomicity: the result is first written to <stem>.tmp/raw.json, then
<stem>.tmp → <stem> via rename. An interrupted run leaves no corrupt
artifacts; the next pass will regenerate them.

Run inside the jupyter-kurpatov-wiki container:
  docker exec -t jupyter-kurpatov-wiki python -u /workspace/notebooks/02_transcribe_incremental.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

from faster_whisper import WhisperModel
from tqdm import tqdm


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def probe_duration(path: Path) -> float:
    """Duration via ffprobe — no decoding."""
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(path),
        ]
    )
    return float(out.strip())


def clean_tmp_dir(tmp_dir: Path) -> None:
    """Wipe a half-written tmp directory left over from an interrupted run."""
    if not tmp_dir.exists():
        return
    for p in tmp_dir.rglob("*"):
        if p.is_file():
            p.unlink()
    for p in sorted(tmp_dir.rglob("*"), reverse=True):
        if p.is_dir():
            p.rmdir()
    tmp_dir.rmdir()


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", default="/workspace/videos",
                    help="Root with video files (recursive scan)")
    ap.add_argument("--out", default="/workspace/vault/raw",
                    help="Where to place transcripts (default: vault/raw)")
    ap.add_argument("--pattern", default="*.mp4",
                    help="Video glob (default: *.mp4)")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--compute", default="float16",
                    choices=["float16", "bfloat16", "int8_float16"])
    ap.add_argument("--beam", type=int, default=5)
    ap.add_argument("--language", default="ru")
    args = ap.parse_args()

    videos_root = Path(args.videos)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    # out_dir mirrors the full hierarchy videos/<...>/<name>.mp4 →
    # vault/raw/<...>/<name>/raw.json
    def out_dir_for(v: Path) -> Path:
        return out_root / v.relative_to(videos_root).with_suffix("")

    # ----- 1. Scan videos + pick the missing ones -----
    all_videos = sorted(videos_root.rglob(args.pattern))
    pending = [v for v in all_videos
               if not (out_dir_for(v) / "raw.json").exists()]

    done_count = len(all_videos) - len(pending)
    print(f"[scan ] videos found: {len(all_videos)}  "
          f"done: {done_count}  pending: {len(pending)}")

    if not pending:
        print("[done ] nothing to do — vault/raw is up to date")
        return

    # ----- 2. Durations up front (for an accurate outer progress bar) -----
    print("[probe] measuring durations via ffprobe...")
    durations = {v: probe_duration(v) for v in pending}
    total_audio = sum(durations.values())
    print(f"[probe] queue: {len(pending)} files, "
          f"{total_audio/3600:.2f}h audio total "
          f"(≈{total_audio*0.05/60:.1f} min wall @ RTF 0.05)")

    # ----- 3. Load the model once for the whole batch -----
    print(f"[load ] {args.model} on cuda ({args.compute})")
    t0 = time.time()
    model = WhisperModel(
        args.model,
        device="cuda",
        compute_type=args.compute,
        download_root="/workspace/models",
    )
    print(f"[load ] done in {time.time() - t0:.1f}s")

    # ----- 4. Transcription with a double progress bar -----
    outer_bar = tqdm(
        total=total_audio,
        desc="TOTAL",
        position=0,
        unit="s",
        dynamic_ncols=True,
        bar_format=(
            "{l_bar}{bar}| {n:.0f}/{total:.0f}s "
            "[{elapsed}<{remaining}]"
        ),
    )

    try:
        for idx, video in enumerate(pending, 1):
            audio_dur = durations[video]
            stem = video.stem
            out_dir = out_dir_for(video)
            tmp_dir = out_dir.parent / f"{out_dir.name}.tmp"
            out_dir.parent.mkdir(parents=True, exist_ok=True)
            clean_tmp_dir(tmp_dir)
            tmp_dir.mkdir(parents=True)

            label = stem if len(stem) <= 55 else stem[:52] + "..."
            label = f"[{idx}/{len(pending)}] {label}"

            inner_bar = tqdm(
                total=audio_dur,
                desc=label,
                position=1,
                leave=False,
                unit="s",
                dynamic_ncols=True,
                bar_format="{l_bar}{bar}| {n:.0f}/{total:.0f}s",
            )

            t_file = time.time()
            segments, info = model.transcribe(
                str(video),
                language=args.language,
                beam_size=args.beam,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                word_timestamps=True,
            )

            raw_segments = []
            processed = 0.0
            for i, seg in enumerate(segments, 1):
                raw_segments.append({
                    "id": i,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "speaker": None,
                    "words": [
                        {"start": w.start, "end": w.end,
                         "word": w.word, "prob": w.probability}
                        for w in (seg.words or [])
                    ],
                })
                step = max(seg.end - processed, 0.0)
                if step > 0:
                    inner_bar.update(step)
                    outer_bar.update(step)
                    processed = seg.end

            # VAD may have trimmed trailing silence — top up the bars to the nominal length.
            tail = max(audio_dur - processed, 0.0)
            if tail > 0:
                inner_bar.update(tail)
                outer_bar.update(tail)

            payload = {
                "info": {
                    "language": info.language,
                    "duration": info.duration,
                    "language_probability": info.language_probability,
                    "source_path": str(video),
                    "model": args.model,
                    "compute_type": args.compute,
                    "beam_size": args.beam,
                    "transcribed_at": utc_now_iso(),
                    "diarized": False,
                },
                "segments": raw_segments,
            }
            (tmp_dir / "raw.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # atomic final rename
            tmp_dir.rename(out_dir)
            inner_bar.close()

            wall = time.time() - t_file
            rtf = wall / max(audio_dur, 1e-6)
            outer_bar.write(
                f"[done ] {stem[:70]} — {len(raw_segments)} segs, "
                f"audio {audio_dur:.0f}s, wall {wall:.0f}s, RTF {rtf:.3f}"
            )

    finally:
        outer_bar.close()

    print(f"\n[done ] processed {len(pending)} videos -> {out_root}")


if __name__ == "__main__":
    main()
