"""Build a fixture for E2E test #2 — production-shape data, compacted transcripts.

Per ADR 0010 + the K1 silent-skip incident:
  Synth tests (3-layer ladder) all pass. Production verify-fails 6/14 in the
  same run. The reproducibility gap must be a function of EITHER (a) data
  shape (real raw.json, real Cyrillic/curly/long-stem paths, real claim
  density, real concept density) OR (b) long-running state (heap/fd/dentry
  pressure after dozens of sequential agents).

This fixture isolates (a): take REAL raw.json files from the K1 raw repo
(same module, same paths, same Whisper output structure), compact each to
~5 segments (~50 s of audio, a few sentences) so each iteration is cheap,
and run the FULL production orchestrator in-process over them.

Whole number of files preserved — the fixture has 4 separate sources, each
processed sequentially in the same Python process, just like production.

Output:
  /tmp/e2e-real-workspace/raw/data/<course>/<module>/<source-N>/raw.json
    (compacted: 5 segments, full info dict, full Cyrillic/curly path)
  /tmp/e2e-real-workspace/wiki/
    (clean clone of kurpatov-wiki at skill-v2 HEAD before K1 commits)

This script runs on the FORGE HOST — not inside the bench container.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

K1_RAW_ROOT = Path("/tmp/k1-pilot/raw")              # source of REAL raw.json files
K1_WIKI_ROOT = Path("/tmp/k1-pilot/wiki")            # source of skills/* and structure
DEFAULT_FIXTURE = Path("/tmp/e2e-real-workspace")

COURSE = "Психолог-консультант"
# Use module 001 — that's where the K1 verify-fails happened.
MODULE = "001 Глубинная психология и психодиагностика в консультировании"

# 4 source stems to process. Picked from the failed-in-K1 set so we stress
# the same paths that broke in production. Compacting kills LLM-time but
# keeps every byte of the path encoding identical.
DEFAULT_STEMS = [
    "006 1.1 Начинаем погружение по внутренний мир",
    "007 1.1 Начинаем погружение во внутренний мир",
    "008 2.1 Кто такой этот загадочный мистер Фрейд?",
    "009 2.1 Кто такой этот загадочный мистер Фрейд_",
]

SEGMENTS_PER_SOURCE = 5


def compact_raw_json(src_path: Path, dst_path: Path, n_segments: int) -> None:
    """Read src raw.json, keep info dict + first n_segments, write to dst."""
    data = json.loads(src_path.read_text(encoding="utf-8"))
    if "info" not in data or "segments" not in data:
        raise RuntimeError(f"unexpected raw.json shape at {src_path}: keys={list(data.keys())}")
    out = {
        "info": dict(data["info"]),
        "segments": data["segments"][:n_segments],
    }
    # Mark this fixture so we never confuse it with production data.
    out["info"]["__fixture__"] = "e2e-real-compacted"
    out["info"]["__original_segments__"] = len(data["segments"])
    out["info"]["__kept_segments__"] = len(out["segments"])
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8")


def _resolve_real_name(parent: Path, candidate: str) -> str:
    """Find the on-disk directory entry matching candidate, accounting for
    NFC vs NFD Unicode normalization. K1 raw data was originally scraped
    on macOS (NFD); our script literals are NFC. Linux preserves the bytes
    verbatim so Path.exists() does not normalize. We list the parent and
    return the actual on-disk name so downstream paths match byte-for-byte."""
    import unicodedata
    target_nfc = unicodedata.normalize("NFC", candidate)
    for entry in parent.iterdir():
        if unicodedata.normalize("NFC", entry.name) == target_nfc:
            return entry.name
    raise RuntimeError(
        f"no entry under {parent} matches {candidate!r} (NFC-normalised); "
        f"available: {[e.name for e in parent.iterdir()][:8]}"
    )


def build_raw_fixture(fixture_root: Path, stems: list[str]) -> list[str]:
    """Populate fixture_root/raw/data/<course>/<module>/<stem>/raw.json with
    compacted copies of the real K1 raw.json files. Returns the resolved
    on-disk stems (NFD-preserving) so the runner can echo them."""
    raw_root = fixture_root / "raw"
    if raw_root.exists():
        shutil.rmtree(raw_root)
    raw_root.mkdir(parents=True)

    # Resolve module name on disk (course is ASCII enough that NFC=NFD).
    src_course_dir = _resolve_real_name(K1_RAW_ROOT / "data", COURSE)
    src_module_dir_name = _resolve_real_name(K1_RAW_ROOT / "data" / src_course_dir, MODULE)
    src_module_dir = K1_RAW_ROOT / "data" / src_course_dir / src_module_dir_name
    # Mirror the on-disk encoding into the fixture so the orchestrator
    # processes byte-identical paths.
    dst_module_dir = raw_root / "data" / src_course_dir / src_module_dir_name
    dst_module_dir.mkdir(parents=True)

    resolved_stems: list[str] = []
    for stem in stems:
        real_stem = _resolve_real_name(src_module_dir, stem)
        resolved_stems.append(real_stem)
        src = src_module_dir / real_stem / "raw.json"
        dst = dst_module_dir / real_stem / "raw.json"
        if not src.exists():
            raise RuntimeError(f"raw.json not found at {src}")
        compact_raw_json(src, dst, SEGMENTS_PER_SOURCE)
        print(f"  compacted {real_stem!r}: "
              f"{src.stat().st_size:,} B -> {dst.stat().st_size:,} B "
              f"({SEGMENTS_PER_SOURCE} segments)", flush=True)
    return resolved_stems

    # Also copy the bare directory layout the orchestrator expects: a
    # `raw` git repo. We make it a real repo so any tooling that does
    # `git -C raw rev-parse HEAD` does not break, but it has no remote.
    subprocess.run(["git", "init", "-q"], cwd=raw_root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=raw_root, check=True)
    subprocess.run(["git", "-c", "user.email=e2e@test", "-c", "user.name=e2e",
                    "commit", "-q", "-m", "fixture: compacted raw"],
                   cwd=raw_root, check=True)


def build_wiki_fixture(fixture_root: Path) -> None:
    """Set up fixture_root/wiki as a fresh clone of the wiki at skill-v2
    HEAD (pre-K1 state). The orchestrator will checkout an experiment
    branch on top of this. We rewrite the remote to a local bare repo
    so commit_and_push_per_source can push without GitHub access."""
    wiki = fixture_root / "wiki"
    bare = fixture_root / "wiki-bare.git"
    if wiki.exists():
        shutil.rmtree(wiki)
    if bare.exists():
        shutil.rmtree(bare)

    # Clone the existing K1 wiki (which already has skill-v2 branch) then
    # reset to skill-v2 HEAD so we drop any K1 experiment commits.
    subprocess.run(["git", "clone", "-q", "--no-local",
                    str(K1_WIKI_ROOT), str(wiki)], check=True)

    # Make sure we have skill-v2 locally and checkout it.
    subprocess.run(["git", "fetch", "-q", "origin",
                    "skill-v2:skill-v2"], cwd=wiki, check=False)
    subprocess.run(["git", "checkout", "-q", "skill-v2"], cwd=wiki, check=True)

    # Make a bare local mirror to act as origin so push succeeds.
    subprocess.run(["git", "clone", "-q", "--bare", str(wiki), str(bare)],
                   check=True)
    subprocess.run(["git", "remote", "set-url", "origin", str(bare)],
                   cwd=wiki, check=True)

    # Sanity: skill-v2 must still be the current branch and pushable.
    head = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                    cwd=wiki, text=True).strip()
    print(f"  wiki HEAD = {head[:8]} on skill-v2; remote -> {bare}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture-root", default=str(DEFAULT_FIXTURE))
    ap.add_argument("--stems", nargs="*", default=DEFAULT_STEMS,
                    help="Source stems to compact. Default: 4 stems from "
                         "the K1 verify-fail cluster.")
    ap.add_argument("--segments", type=int, default=SEGMENTS_PER_SOURCE)
    args = ap.parse_args()

    fixture_root = Path(args.fixture_root)
    fixture_root.mkdir(parents=True, exist_ok=True)
    print(f"[fixture] root = {fixture_root}", flush=True)
    print(f"[fixture] {len(args.stems)} sources × {args.segments} segments each",
          flush=True)

    print(f"[fixture] step 1/2: compacting raw.json files…", flush=True)
    resolved_stems = build_raw_fixture(fixture_root, args.stems)

    print(f"[fixture] step 2/2: cloning wiki at skill-v2 HEAD…", flush=True)
    build_wiki_fixture(fixture_root)

    print(f"[fixture] done. modules to process:", flush=True)
    print(f"  course         = {COURSE!r}", flush=True)
    print(f"  module         = {MODULE!r}", flush=True)
    print(f"  stems (input)  = {args.stems}", flush=True)
    print(f"  stems (on-disk NFD-preserving) = {resolved_stems}", flush=True)


if __name__ == "__main__":
    main()
