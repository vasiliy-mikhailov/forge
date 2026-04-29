# Cross-platform paths: NFC/NFD policy

Implementation contract for [ADR 0011](../adr/0011-nfc-nfd-cross-platform-paths.md).

## TL;DR

- Forge canonical filename form on disk is **NFC**.
- Data scraped or produced on macOS arrives in NFD. Normalise at
  ingest, NEVER inside hot paths.
- Python literals, JSON, and LLM-emitted paths are NFC by default.
- `Path.exists`, `open`, `os.stat`, and bash do NOT normalise. Byte
  mismatch ⇒ "No such file or directory".
- LLM agents must `ls` first and use the actual on-disk byte
  sequence, never retype Cyrillic into bash.

## When this matters

You touch this policy if your code path:

- Reads a filesystem with Cyrillic (or any non-ASCII) names that
  may have originated on macOS — `kurpatov-wiki-raw`, any other
  scrape that came off the architect's laptop.
- Constructs paths from configuration values, JSON entries, env
  vars, or LLM tool-call arguments and then opens/stats them.
- Drives an LLM agent that issues bash or python commands against
  Cyrillic paths.
- Writes a synth fixture for any of the above and wants the test
  to actually reproduce production behaviour.

If your code is ASCII-only, ignore this doc.

## Helpers

Drop these into any module that constructs paths from non-ASCII
strings, or import them from `phase-c-…/wiki-bench/orchestrator/path_helpers.py`
(canonical home for forge labs).

```python
import unicodedata
from pathlib import Path


def nfc(s: str) -> str:
    """Normalise a string to NFC. Forge canonical form."""
    return unicodedata.normalize("NFC", s)


def nfd(s: str) -> str:
    """Normalise to NFD. Use only when matching macOS-origin filenames
    that have not yet been ingested through the M1 normalisation pass."""
    return unicodedata.normalize("NFD", s)


def find_nfc(parent: Path, candidate: str) -> str:
    """Find the actual on-disk entry under `parent` whose name
    NFC-normalises to NFC(candidate). Returns the on-disk byte
    sequence verbatim — DO NOT pass `candidate` further; pass the
    return value. Raises if no match.

    Use this whenever you receive a non-ASCII path from a config
    file, JSON, env var, or LLM and need to interact with it on a
    filesystem that may store NFD bytes.
    """
    target = nfc(candidate)
    for entry in parent.iterdir():
        if nfc(entry.name) == target:
            return entry.name
    raise FileNotFoundError(
        f"no NFC-equivalent of {candidate!r} under {parent}; "
        f"have {[e.name for e in parent.iterdir()][:8]}"
    )
```

## M1 — Ingestion

When new macOS-origin data lands on Linux for forge use, the
ingest pipeline normalises filenames to NFC as the very first
step. Pseudocode:

```python
import os, unicodedata
def renormalise_to_nfc(root):
    """Walk `root` bottom-up; rename any entry whose name is not in NFC."""
    for d, dirs, files in os.walk(root, topdown=False):
        for n in files + dirs:
            target = unicodedata.normalize("NFC", n)
            if target != n:
                os.rename(os.path.join(d, n), os.path.join(d, target))
```

Run as a one-shot pass on existing legacy data, then again as a
post-`rsync` step in any future ingest job.

The renormalisation is recorded in a git commit on the affected
data repo with message `"ingest: renormalise N entries from NFD to NFC"`.

## M2 — Code authoring

Three rules:

1. **String equality on filenames is unreliable.** Compare via
   `nfc(a) == nfc(b)` whenever either side may have come from a
   non-ASCII filesystem.
2. **Constructed paths must round-trip through the filesystem.**
   If you have a string from JSON / env / LLM and need to open the
   file, `find_nfc(parent, that_string)` first; pass the return.
3. **`os.listdir` / `Path.iterdir` is byte-faithful.** Treat its
   output as ground truth and use it verbatim downstream. Never
   "clean it up" by NFC-normalising before opening.

## M3 — LLM agent prompts

Every agent prompt that handles paths with non-ASCII content
must include a section like:

```
⚠️ NFC/NFD HAZARD ON THIS FILESYSTEM

Filenames on /workspace may be encoded in NFD (decomposed form).
The path I show you in this prompt is in NFC. Bash and Python's
open() do NOT normalise — they compare bytes. If you type a
Cyrillic path literally and bash says "No such file or directory",
that is almost certainly NFC↔NFD mismatch, NOT a missing file.

Recovery rules:
1. NEVER retype a non-ASCII path literally. Instead:
   - `ls "$parent"` then copy the actual on-disk name
   - or use a shell glob: `*мир*` (the kernel matches bytes)
   - or pass the raw_path I gave you via env/argv, not via a
     code literal: `python3 - <<EOF` blocks lose nothing.
2. If you must construct a Cyrillic path in code, use:
     for entry in os.listdir(parent):
         if unicodedata.normalize("NFC", entry) == \
            unicodedata.normalize("NFC", candidate):
             real = entry
             break
3. Once you have the real on-disk name, USE IT VERBATIM. Do not
   round-trip it through any helper that might normalise.

Sentinel: if `cd "<cyrillic>"` fails, IMMEDIATELY `ls -la "<parent>"`
and use the names ls printed. Do not retry the same literal path.
```

## M4 — Test fixtures

Any synth fixture that derives paths from production data must
preserve the on-disk Unicode form of that data. Helpers like
`build_e2e_real_fixture.py::_resolve_real_name` round-trip via
`os.listdir` and pass the actual on-disk bytes through. Tests
that ASCII-mock the paths (e.g. `course/module-a`) are still
valuable for the polling logic they test, but cannot stand in
for production fidelity on the NFC/NFD axis.

## M5 — Lint

A small CI check (`tools/nfd_check.py`) walks a directory and
reports any entries whose name is not in canonical NFC. Non-empty
report fails the check; the operator either renames or explicitly
accepts.

```python
#!/usr/bin/env python3
"""Walk a path; print every entry whose name is not in NFC."""
import os, sys, unicodedata

def main(root):
    bad = []
    for d, dirs, files in os.walk(root):
        for n in files + dirs:
            if unicodedata.normalize("NFC", n) != n:
                bad.append(os.path.join(d, n))
    for b in bad:
        print(b)
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
```

## Why NFC and not NFD

- Python literals, JSON spec, HTTP, web tooling all default to NFC.
- LLM tokenizers normalise to NFC; outputs match.
- NFC is shorter on disk (single codepoint per composed character).
- macOS APFS no longer requires NFD; modern macOS tooling tolerates
  NFC just fine. The historical reason to keep NFD (HFS+
  enforcement) is gone.
- Linux preserves whatever bytes you give it — NFC writes survive
  unchanged.

The only downside is migrating existing macOS-origin data once.
