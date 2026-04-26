You are starting in a fresh, empty working directory inside a Linux sandbox (Docker container). You have shell, file I/O, and HTTPS access. Your LLM endpoint is configured for you; just call it normally.

Model served by the inference endpoint: __INFERENCE_SERVED_NAME__ (use this verbatim as the slug for STEP 0; do NOT introspect)

This is **experiment D7-rev2** — same skill v2 (12-step ritual + helper scripts) as D7, plus three pre-baked fixes from the D7 attempt #1 post-mortem:
1. SKILL.md path bug fixed (helpers at `skills/benchmark/list_sources.py` and `extract_transcript.py`, not under `scripts/`).
2. `factcheck.py` rewrite: now uses system curl with `LD_LIBRARY_PATH=""` as primary path; the PyInstaller-bundled libssl conflict that broke D7 attempt #1 is no longer an issue. Just call `python3 wiki/skills/benchmark/scripts/factcheck.py "<claim>"` and it returns valid JSON first-try.
3. Build-time HTTPS smoke in the Docker image — by the time you start, both `urllib` and `curl` are verified to reach Wikipedia. Do not waste time troubleshooting network.

Clone both repos via HTTPS using the GitHub token at the bottom of this prompt:

```
TOKEN=<see end of prompt>
git clone https://x-access-token:$TOKEN@github.com/vasiliy-mikhailov/kurpatov-wiki-raw.git raw
git clone https://x-access-token:$TOKEN@github.com/vasiliy-mikhailov/kurpatov-wiki-wiki.git wiki

# IMPORTANT: switch to skill-v2 branch — it has the v2 skill + helper scripts.
cd wiki && git checkout skill-v2 && git pull --ff-only && cd ..
```

Then read `wiki/skills/benchmark/SKILL.md` (which is now the v2 ritual) and execute it end-to-end. Begin with STEP 0.

When the skill instructs `git push origin "$BRANCH"`, use the same HTTPS+token form (the remote should already be set correctly by the clone above). Branch name format for this experiment is `experiment/D7-rev2-<YYYY-MM-DD>-<served-name>` (note the `experiment/` prefix and the `rev2` infix).

## Filesystem layout (cheatsheet — do NOT re-derive)

The course tree under `raw/data/` and the wiki tree under `wiki/data/` use **Cyrillic** course/module names. **DO NOT translate paths to English. DO NOT romanize.** Use the exact Cyrillic strings from the raw filesystem layout.

Canonical paths (read these literally; do not invent variants):

- Course directory: `Психолог-консультант`
- Default module: `005 Природа внутренних конфликтов. Базовые психологические потребности`
- Source articles live at: `wiki/data/sources/Психолог-консультант/<module-name>/<source-slug>.md`
- Concept articles live at: `wiki/data/concepts/<concept-slug>.md` (concept slugs ARE in English — these are taxonomy keys, not paths derived from course/module names)
- Concept index: `wiki/data/concept-index.json`

If you find yourself typing `Psychologist-consultant/` or `05-conflicts/` anywhere — STOP. That is wrong. Use `Психолог-консультант/` and `005 Природа внутренних конфликтов. Базовые психологические потребности/` literally. The agent on D7 attempt #1 silently translated these paths to English mid-run; **the resulting source articles were rejected by the grader as off-spec**. This is non-recoverable — don't do it.

If your shell tool struggles with Cyrillic in `bash` arguments, that's exactly why the helper scripts exist:

```
python3 wiki/skills/benchmark/list_sources.py            # ← top of skills/benchmark/, NOT scripts/
python3 wiki/skills/benchmark/extract_transcript.py 0    # ← top of skills/benchmark/, NOT scripts/
```

Both are pure-ASCII command lines that walk the Cyrillic-pathed tree internally. Use them instead of typing Cyrillic into bash.

## Mandatory contracts (script side)

Two helper scripts are mandatory contracts in v2 and live at `wiki/skills/benchmark/scripts/`:
- `get_known_claims.py` — required call per source for REPEATED detection. Call it once per source before classification.
- `factcheck.py "<claim>"` — required call per empirical claim for fact-check + URL citations. URLs in `## Claims` MUST come from this script's output; no inventing URLs from memory.

Their absence means you cannot complete the source — surface to operator.

## What "completed" means for this experiment

A source is *complete* only if its `source-XXX.md` has:
- valid YAML frontmatter at the top (no `---` / `# Title` shape; the literal frontmatter format from skill-v2),
- the 5 mandatory sections in order: `## TL;DR`, `## Лекция (пересказ: только NEW и проверенное)`, `## Claims — provenance and fact-check`, `## New ideas (verified)`, `## All ideas`,
- every claim in `## Claims` carrying exactly one marker `[NEW] / [REPEATED (from: <slug>)] / [CONTRADICTS_FACTS]`,
- every empirical claim with at least one `https://*.wikipedia.org/...` URL inline,
- the deterministic bash self-verify (step 12) passing before commit.

Do not commit a source whose self-verify reports any mismatch. Re-write the failing section first.
