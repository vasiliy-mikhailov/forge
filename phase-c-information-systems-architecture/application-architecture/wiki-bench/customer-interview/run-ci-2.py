#!/usr/bin/env python3
"""CI-2 driver: run customer-interview readings × 5 personas × N lectures.

Per ADR 0016 (Wiki Customer cycle) + architect call (2026-05-02): use
Claude API (not Blackwell qwen3.6-27b) for higher persona-voice fidelity.
Pain ledger length: ~10% of source (per architect call; ADR 0023
TTS framing).

Outputs land in PRIVATE repo per ADR 0018:
  kurpatov-wiki-wiki/metadata/customer-pains/<persona>/<lecture-stem>.md

Usage:
  # Probe — 1 persona × 1 lecture (Step 0 falsifier-first)
  python3 run-ci-2.py --persona academic-researcher \
                      --module 001 --lecture-index 1 \
                      --dry-run    # show prompt, no API call

  # Full sweep — 5 personas × 44 lectures (modules 000 + 001)
  python3 run-ci-2.py --all-personas --modules 000,001

Requires:
  - ANTHROPIC_API_KEY env var
  - anthropic SDK (already installed: pip install anthropic --break-system-packages)
  - kurpatov-wiki-raw mounted at sibling path ../../../../../../kurpatov-wiki-raw
  - kurpatov-wiki-wiki mounted at sibling path ../../../../../../kurpatov-wiki-wiki
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
FORGE = LAB_DIR.parents[3]  # phase-c/.../wiki-bench/customer-interview → forge root
KURPATOV_RAW = FORGE.parent / 'kurpatov-wiki-raw' / 'data' / 'Психолог-консультант'
KURPATOV_WIKI = FORGE.parent / 'kurpatov-wiki-wiki' / 'metadata' / 'customer-pains'

PERSONAS_DIR = FORGE / 'phase-b-business-architecture' / 'roles' / 'customers'
PERSONAS = ['academic-researcher', 'entry-level-student', 'lay-curious-reader',
            'time-poor-reader', 'working-psychologist']

MODULE_DIRS = {
    '000': '000 Путеводитель по программе',
    '001': '001 Глубинная психология и психодиагностика в консультировании',
}

PROMPT_SYSTEM = '''You are imitating a specific reader of an Andrey Kurpatov
psychology lecture. Your task: read the lecture transcript and write a per-persona
pain ledger documenting what hurt, what worked, and how the wiki version of this
lecture could be improved. The pain ledger goes into kurpatov-wiki-wiki private repo
for the Wiki PM to cross-tabulate across personas (CI-3..5 of the customer-interview
cycle defined in ADR 0016).

Persona file (your character — read this CAREFULLY before writing; voice MUST match):
{persona_md}

Lecture metadata:
- Module: {module_name}
- Lecture: {lecture_stem}
- Source duration estimate: {duration_est} min
- Source word count: {word_count}
- Format: {format_hint}

Output requirements:
1. Write IN CHARACTER per the persona file's Voice fingerprint section.
2. Length target: ~10% of source word count = ~{target_words} words.
3. Structure (markdown):
   ```
   # Pain ledger — {persona} × {lecture_stem}

   Persona: {persona} (../../../roles/customers/{persona}.md)
   Lecture: {module_name} / {lecture_stem}
   Reading mode: <skim|deep|re-read — match persona Reading mode section>
   Time spent: <approximate>

   ## Pains

   ### P1 — <one-line title>
   - **Severity**: blocking|moderate|mild
   - **Where**: <segment id or paragraph from raw.json>
   - **Quality dimension**: <Voice / Reading speed / Dedup / Fact-check / Concept-graph / Reproducibility / Transcription / Requirement traceability>
   - **What I noticed**: <persona-voice prose, 2-4 sentences>
   - **What would help**: <2-3 sentences>

   ### P2 — ...
   ...

   ## Wins (what already works)
   - <bullet list, terse>

   ## Overall verdict
   - <2-3 sentence persona-voice summary>
   ```
4. Severity calibration per the persona's file (blocking / moderate / mild).
5. Each pain MUST cite a specific segment id or paragraph location from the
   raw.json. The persona may quote a verbatim phrase if it sharpens the pain
   (sparingly — privacy boundary per ADR 0018 still allows brief quotes for
   the pain ledger which lives in the PRIVATE repo).
6. Anti-examples in the persona file are negative-space — DO NOT do those.
7. Sample pain entry in the persona file is positive-space — match its density.

Lecture transcript follows. Read it as the persona would (per Reading mode
section), then write the pain ledger.
'''


def load_persona(persona_slug):
    p = PERSONAS_DIR / f'{persona_slug}.md'
    return p.read_text(encoding='utf-8')


def list_lectures(module_id):
    """Return sorted list of (lecture_stem, raw_json_path) tuples."""
    mod_dir = KURPATOV_RAW / MODULE_DIRS[module_id]
    if not mod_dir.exists():
        return []
    out = []
    for sub in sorted(mod_dir.iterdir()):
        if not sub.is_dir():
            continue
        rj = sub / 'raw.json'
        if rj.exists():
            out.append((sub.name, rj))
    return out


def load_lecture(raw_json_path):
    """Return (segments_text, segment_count, word_count_est, duration_est_min)."""
    with raw_json_path.open(encoding='utf-8') as f:
        d = json.load(f)
    segs = d.get('segments', [])
    segments_text = '\n'.join(f'[seg {s.get("id", i)}] {s.get("text", "")}'
                              for i, s in enumerate(segs))
    word_count = sum(len(s.get('text', '').split()) for s in segs)
    duration_est = max(1, word_count // 150)  # rough: 150 wpm spoken
    return segments_text, len(segs), word_count, duration_est


def call_claude(prompt_system, lecture_text, model='claude-sonnet-4-6'):
    """Call Anthropic API. Returns response text."""
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=prompt_system,
        messages=[{'role': 'user', 'content': lecture_text}],
    )
    return response.content[0].text


def write_ledger(persona, lecture_stem, ledger_md):
    out_dir = KURPATOV_WIKI / persona
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r'[^\w\-]', '_', lecture_stem)[:80]
    out_path = out_dir / f'{safe_stem}.md'
    out_path.write_text(ledger_md, encoding='utf-8')
    return out_path


def run_one(persona, module_id, lecture_stem, raw_json_path, dry_run=False, model='claude-sonnet-4-6'):
    persona_md = load_persona(persona)
    lecture_text, seg_count, word_count, duration_est = load_lecture(raw_json_path)
    target_words = max(150, word_count // 10)
    module_name = MODULE_DIRS[module_id]
    prompt = PROMPT_SYSTEM.format(
        persona_md=persona_md,
        persona=persona,
        module_name=module_name,
        lecture_stem=lecture_stem,
        duration_est=duration_est,
        word_count=word_count,
        format_hint='spoken (raw.json from faster-whisper)' if word_count > 3000 else 'short / written',
        target_words=target_words,
    )
    if dry_run:
        print(f'\n=== DRY RUN: {persona} × {module_id}/{lecture_stem} ===')
        print(f'Lecture: {seg_count} segments, {word_count} words, ~{duration_est} min, target ledger: {target_words} words')
        print(f'Prompt size: ~{len(prompt) // 4} tokens (system) + ~{len(lecture_text) // 4} tokens (user)')
        print(f'Output target: {KURPATOV_WIKI / persona / lecture_stem}.md')
        return None
    print(f'  → calling Claude API...', end=' ', flush=True)
    t0 = time.time()
    ledger = call_claude(prompt, lecture_text, model=model)
    elapsed = time.time() - t0
    out_path = write_ledger(persona, lecture_stem, ledger)
    actual_words = len(ledger.split())
    print(f'OK ({elapsed:.1f}s, {actual_words}w → {out_path})')
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--persona', choices=PERSONAS)
    ap.add_argument('--all-personas', action='store_true')
    ap.add_argument('--module', choices=list(MODULE_DIRS), action='append')
    ap.add_argument('--modules', help='Comma-separated module IDs (e.g. 000,001)')
    ap.add_argument('--lecture-index', type=int, help='Pick Nth lecture in module (0-indexed)')
    ap.add_argument('--dry-run', action='store_true', help='Show prompt, no API call')
    ap.add_argument('--model', default='claude-sonnet-4-6')
    ap.add_argument('--limit', type=int, help='Stop after N sessions (for sample sweep)')
    args = ap.parse_args()

    if args.modules:
        modules = args.modules.split(',')
    elif args.module:
        modules = args.module
    else:
        modules = ['000', '001']

    if args.all_personas:
        personas = PERSONAS
    elif args.persona:
        personas = [args.persona]
    else:
        sys.exit('--persona <slug> OR --all-personas required')

    # Build session list
    sessions = []
    for module_id in modules:
        lectures = list_lectures(module_id)
        if args.lecture_index is not None:
            lectures = [lectures[args.lecture_index]]
        for lecture_stem, raw_json in lectures:
            for persona in personas:
                # Skip if ledger already exists (resumable sweeps)
                safe_stem = re.sub(r'[^\w\-]', '_', lecture_stem)[:80]
                out = KURPATOV_WIKI / persona / f'{safe_stem}.md'
                if out.exists():
                    continue
                sessions.append((persona, module_id, lecture_stem, raw_json))

    if args.limit:
        sessions = sessions[:args.limit]

    print(f'CI-2 sessions queued: {len(sessions)} ({len(personas)} personas × {sum(len(list_lectures(m)) for m in modules)} lectures - already-done)')
    if not sessions:
        return

    if not args.dry_run and not os.environ.get('ANTHROPIC_API_KEY'):
        sys.exit('ANTHROPIC_API_KEY not set. Run with --dry-run to preview, or set the key first.')

    for i, (persona, module_id, lecture_stem, raw_json) in enumerate(sessions, 1):
        print(f'[{i}/{len(sessions)}] {persona} × {module_id} / {lecture_stem}')
        try:
            run_one(persona, module_id, lecture_stem, raw_json, dry_run=args.dry_run, model=args.model)
        except KeyboardInterrupt:
            print('\nInterrupted; partial sweep saved.')
            sys.exit(130)
        except Exception as e:
            print(f'  FAIL: {type(e).__name__}: {e}')


if __name__ == '__main__':
    main()
