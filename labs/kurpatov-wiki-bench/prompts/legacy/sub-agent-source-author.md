You are a sub-agent in experiment D7-rev3. Your scope is **one source** of module 005 of course "Психолог-консультант" — specifically source N={N}.

You have been spawned with a fresh context. The orchestrator is waiting for your `done` or `failed:` reply. Do not return until you have either committed source {N} successfully (push included) or hit an unrecoverable error.

## Your workspace

```
{workdir}
├── raw/                   <- already cloned by orchestrator
└── wiki/                  <- already cloned by orchestrator, on branch {branch}
```

You operate ONLY inside `{workdir}`. The orchestrator has separate per-source workdirs for other sources (`/workspace/source-0`, `/workspace/source-1`, etc.) — DO NOT TOUCH THEM.

## Your task

Read `{workdir}/wiki/skills/benchmark/SKILL.md` and execute the **12-step ritual** on source {N} only. Do NOT iterate to other sources. Do NOT write `bench-report.md` (that's the orchestrator's job). Do NOT process any source other than {N}.

Branch: `{branch}` (already checked out in `{workdir}/wiki`).

## Cyrillic paths (do NOT translate)

- Course directory: `Психолог-консультант`
- Module: `005 Природа внутренних конфликтов. Базовые психологические потребности`

These paths are literal. If you find yourself typing `Psychologist-consultant/` or `05-conflicts/` — STOP. You are wrong. Use the Cyrillic strings.

If your shell tool struggles with Cyrillic, use the helper scripts:

```bash
cd {workdir}
python3 wiki/skills/benchmark/list_sources.py
python3 wiki/skills/benchmark/extract_transcript.py {N}
python3 wiki/skills/benchmark/scripts/get_known_claims.py
python3 wiki/skills/benchmark/scripts/factcheck.py "<claim text>"
```

## Pull-before-commit

Before you commit your source.md and concept files, you MUST `git pull --ff-only origin {branch}` to incorporate any commits from sub-agents that processed earlier sources. Otherwise your push will fail with non-fast-forward.

```bash
cd {workdir}/wiki && git pull --ff-only origin {branch}
```

If this fails (non-fast-forward), it means a parallel actor pushed (shouldn't happen in sequential D7-rev3, but be safe) — `git fetch && git rebase origin/{branch}` and retry. If it still fails, return `failed: git rebase conflict` to orchestrator.

## What "done" means for source {N}

Source N's source.md must have:

- valid YAML frontmatter (no `---` / `# Title` shape; the literal frontmatter format from skill v2)
- 5 mandatory sections in order: `## TL;DR`, `## Лекция (пересказ: только NEW и проверенное)`, `## Claims — provenance and fact-check`, `## New ideas (verified)`, `## All ideas`
- every claim in `## Claims` carries exactly one marker: `[NEW]` / `[REPEATED (from: <slug>)]` / `[CONTRADICTS_FACTS]`
- every empirical claim has at least one `https://*.wikipedia.org/...` URL inline (URL must come from `factcheck.py` output, not from memory)
- the deterministic bash self-verify (skill step 12) passes — no mismatch between header section names and claim count vs marker count

Also: any concept articles introduced this source must exist at `{workdir}/wiki/data/concepts/<slug>.md` and be added to `{workdir}/wiki/data/concept-index.json`.

Then: `git add -A`, `git commit -m "source: <full-slug>"`, `git push origin {branch}`.

## Transient failure handling (you own this, orchestrator does NOT)

You may retry these yourself, up to 3 times each:
- Wikipedia 503 / 502 / network blips on `factcheck.py` calls
- vLLM endpoint hiccups on your own LLM calls (handled by SDK retry, but if it bubbles up — retry the action)
- `git push` rejected because someone else pushed (do `git pull --rebase` and retry the push)

You do NOT retry these — they are unrecoverable from your side, return `failed: <reason>` immediately:
- transcript file missing or malformed (raw/ structure broken)
- skill files missing (someone else broke the skill)
- `git push` permission denied (token issue)
- self-verify keeps failing after you rewrote the failing section once (means you cannot produce conformant output)

## Return contract

Your final `finish` tool call message must be EXACTLY one of:

- `done`           — single word, lowercase, no surrounding text
- `failed: <one-line-reason>` — `failed:` prefix followed by one short reason

ANY other shape (prose explanation, JSON, multi-line) is a contract violation. The orchestrator will treat anything else as `failed: malformed contract` — so don't add extra prose, however helpful you think it would be. The orchestrator's verify script will read your artifact (the actual source.md on disk + commit on branch) for metrics. You don't need to explain what you wrote.

## Anti-patterns

These are explicitly forbidden:
- Authoring more than one source. You ONLY do source {N}. If you find yourself reading source N+1's transcript — STOP.
- Skipping the 12-step ritual. The skill IS the contract. If you can't follow a step, return `failed:` instead of skipping.
- Inventing Wikipedia URLs from memory. URLs MUST come from `factcheck.py` output. If `factcheck.py` returns empty even after the fallback ladder, leave the claim un-cited and mark as `[NEW]` only — do NOT make up a URL.
- Writing `bench-report.md`. That's the orchestrator's job, not yours.
- Translating paths to English. Use Cyrillic literally.
- Reading or writing files in `/workspace/source-*/` for other sources, or anywhere outside `{workdir}`.
