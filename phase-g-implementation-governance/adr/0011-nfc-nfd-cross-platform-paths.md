# ADR 0011 — NFC/NFD Unicode normalization on cross-platform paths

Status: Accepted
Date: 2026-04-29
Phase: G (implementation governance)
Related: P6 (architecture-principles.md), wiki-bench ADR 0010, K1 verify-fail post-mortem

## Context

Forge development starts on macOS (the architect's primary workstation)
and continues on Linux (`mikhailov.tech`, all forge services). Data
produced or scraped on macOS is shipped to Linux verbatim by `scp`,
`rsync`, or `git`. Cyrillic-named files — and forge has many of them
(course modules, lecture stems, concept slugs in Russian) — survive
the trip with their **bytes** preserved but their **Unicode normal
form** unchanged from whatever macOS wrote.

macOS HFS+ historically required filenames in NFD (decomposed:
`й` = `и` + COMBINING BREVE = 4 bytes). APFS no longer enforces NFD
at the filesystem level, but most macOS tooling — Finder, Spotlight,
the system Python, third-party scrapers — still emits NFD. Python
literals, JSON dumps, and **LLM tokenizer outputs** default to NFC
(precomposed: `й` = single codepoint = 2 bytes). Linux filesystems
preserve bytes as-is and **do not normalize at lookup time**:
`Path("…NFC…").exists()` returns False against a `…NFD…` directory
entry, and bash's `cd "…NFC…"` returns "No such file or directory".

The K1 verify-fail bug (2026-04-29) was this. Six of fourteen module-001
sources verify-failed because:

1. K1 raw data was scraped on macOS — every Cyrillic directory name
   on disk is NFD.
2. The orchestrator's `list_sources.py` reads the filesystem with
   `os.listdir`, so the `raw_path` it puts into the agent's task
   message is byte-faithful NFD.
3. The LLM tokenizer, on receiving the prompt, **normalises Cyrillic
   to NFC for token-level efficiency**. When the LLM emits
   `cd "/workspace/.../мир/"` in its bash actions, the bytes are NFC.
4. Bash inside the bench container fails with "No such file or
   directory" against an NFD on-disk filesystem. The agent retries,
   sometimes recovers (uses `ls` and parses the actual on-disk
   names), often does not — and gives up before writing source.md.
5. `verify_source` polls the NFD path (correctly), finds nothing,
   reports verify-fail.

K1 SRCs 8, 15, 16, 17 succeeded because the agent happened to use
`ls` or shell globs first and read the NFD names off the filesystem.
K1 SRCs 9-14 failed because the LLM typed NFC paths and never
recovered. The probability is non-zero, intermittent, and very hard
to reproduce without real Cyrillic data — which is why the synth
ladder (with ASCII paths only) all passed, and only the e2e test #2
with **real K1 raw.json data** surfaced it within minutes.

## Decision

Treat NFC/NFD mismatch as a **first-class cross-platform-development
hazard** in forge. Apply mitigations at every layer that crosses the
macOS → Linux boundary or the Python-literal → on-disk-bytes boundary
or the LLM → filesystem boundary.

### M1 — Data ingestion: normalise on the way in

When data scraped or produced on macOS lands on Linux for forge use,
the receiving job MUST normalise filenames to a single canonical
form. **Forge canonical form is NFC** (matches Python literals, JSON
spec, LLM tokenizer outputs, and is shorter on disk). Implemented as
a helper in `phase-g-implementation-governance/policies/cross-platform-paths.md`.

Existing data already on disk in NFD (the K1 raw repo, any prior
macOS-scraped corpus) is brought into compliance via a one-shot
rename pass; new data is normalised at ingest time.

### M2 — Code authoring: don't trust string equality, normalise

Any Python code that constructs a path from a configuration value,
JSON entry, or LLM output and then calls `Path.exists`, `open`,
`os.stat`, etc. MUST normalise the constructed path **and** the
on-disk discovery output to the same form before comparison. The
helper `nfc(s)` and `find_nfc(parent, candidate)` (see policy doc)
are the canonical entry points.

### M3 — LLM agent prompts: explicit warning + recovery contract

Any agent prompt whose work involves filesystem paths with non-ASCII
characters MUST include an NFC/NFD section telling the agent:

- Filesystem entries on this host MAY be in NFD even though the
  prompt itself shows NFC. **Never type a non-ASCII path literally
  into bash or python**. Instead: `ls` the parent and use the actual
  on-disk byte sequence, or pass paths via env vars/argv (not via
  source-code literals).
- If a `cd`, `cat`, `ls`, or `python -c "open(...)"` returns "No
  such file or directory" on a Cyrillic path, the path is almost
  certainly NFC-vs-NFD mismatched. The recovery is: `ls` the parent,
  use the actual on-disk name (don't retype it), or use a shell glob
  (`*мир*`) which lets the kernel handle byte matching.

This warning is added to every agent prompt that handles paths in
`run-d8-pilot.py` (source-author, concept-curator, fact-checker).

### M4 — Test fidelity: synth fixtures must include NFD

Per ADR 0010 (test environments match production), any test fixture
involving filesystem paths derived from production data MUST preserve
the on-disk Unicode normalization of that data. The synth ladder
unit + integration tests previously used ASCII paths and missed this
class of bug. The e2e #2 fixture (`build_e2e_real_fixture.py`)
preserves NFD via `os.listdir` round-trip and is the new floor for
fidelity in any test that touches Cyrillic paths.

### M5 — Detection: lint that surfaces mismatches

A linter `nfd_check.py` walks a directory and reports any entries
whose name is not in canonical NFC form. Run as part of CI / pre-
publish checks. A non-empty report fails the check; the operator
either renames or explicitly accepts the NFD names with a reason.

## Consequences

- macOS-origin Cyrillic data ingested into forge is renamed to NFC
  at ingest. Existing NFD data gets a one-shot migration with a
  recorded git commit in the affected repo.
- Forge LLM agents recover automatically from NFC↔NFD mismatches
  via the prompt contract; the bug becomes an explicit failure-mode
  the agent knows how to handle, not an invisible source of
  intermittent verify-fails.
- Tests that touch Cyrillic paths cost a tiny bit more (round-trip
  via `os.listdir`) but become trustworthy; the synth/production
  reproducibility gap captured in ADR 0010 is closed for this class
  of bug.
- Cost: low — three helper functions, one prompt section per
  affected agent, one CI lint.

## Anti-patterns rejected

- **"Just normalise everywhere".** Universal NFC rewrites break any
  caller that holds an NFD reference (e.g. external git repos
  cloned from macOS-origin upstreams). Normalise at ingest, lint at
  CI, and don't touch already-published data without an explicit
  migration ADR.
- **"The LLM should figure it out".** The LLM tokenizer is trained
  on internet-scale text and standardises to NFC; it cannot reason
  its way out of byte-level mismatch with the filesystem. The
  agent needs an explicit recovery contract, not "be more careful".
- **"Use ASCII slugs everywhere".** Russian course content has
  Cyrillic-only metadata. Forcing ASCII slugs would corrupt the
  source-of-truth and make the wiki unreadable to its target user.
- **"Set LANG/LC_ALL".** Locale settings affect collation and
  tooling output, not on-disk byte matching. They do not fix this.

## Why phase-g and not phase-preliminary

This is an implementation-governance concern (how forge code is
written, tested, and operated), not a top-level architectural
constraint. P6 ("completeness over availability") is the principle
this ADR serves — silent NFC/NFD failures violate P6 because they
cause silent skips in compiled artifacts. ADR 0011 is the concrete
implementation contract that makes P6 enforceable for cross-platform
data.


## Motivation

Per [P7](../../phase-preliminary/architecture-principles.md) — backfit:

- **Driver**: K1 silent-skip — macOS NFD vs LLM NFC mismatch
  (P6 violation).
- **Goal**: Service operation (P6 enforced).
- **Outcome**: NFC normalisation at every cross-platform
  boundary; per phase-g-…/policies/cross-platform-paths.md.
