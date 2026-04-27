# Concept article template — post-mortem of D7-rev3 / D8-pilot drift

**Status:** WITHDRAWN
**Date:** 2026-04-27 (post-mortem update)
**Original claim (2026-04-26):** "skill v2 SKILL.md never specified
concept-page structure" — **WRONG**. Skill v2 already had a complete
contract via:
- `wiki/skills/benchmark/SKILL.md` Step 13 ("Concept articles + index + commit")
- `wiki/prompts/concept-article.md` (full first-introduction prompt)
- `wiki/data/concepts/_template.md` (skeletal template)

The canonical skill v2 concept shape:
```yaml
---
slug:
first_introduced_in:
touched_by: [...]
---
# Title

## Definition

## Contributions by source     ← OR "## Contributions by video" — wiki has both
### <full source slug>
- bullet
- See [<short title>](../sources/<slug>.md). [mm:ss]

## Related concepts
- [other-slug](other-slug.md) — relationship.
```

**My D7-rev3 deviation that propagated to D8 pilot v1:**
- ❌ Used `## Touched in sources` instead of `## Contributions by source`
- ❌ Used `## See also` instead of `## Related concepts`
- ❌ Used `introduced_in:` instead of `first_introduced_in:`
- ❌ Wrote `## Touched in sources` with bullet-per-source instead of
  `### <source-slug>` sub-sections
- ❌ Concept-curator only called for newly-introduced concepts; the
  spec is clear: also append a `### <slug>` sub-section to existing
  concepts (cross-source contribution log).
- ❌ Skipped `concept-index.json:processed_sources` updates.

**Why I missed it:** `bench_grade.py` had
`REQUIRED_CONCEPT_SECTIONS = ["## Definition"]` only — too lenient.
My D7-rev3 concepts passed L1, so I assumed there was no spec to
follow. I wrote my own ("v3") instead of reading
`wiki/prompts/concept-article.md`.

**Recovery (in D8 pilot v2 / forge:main):**
1. Concept-curator prompt rewritten to follow canonical skill v2 shape.
2. Source-author prompt rewritten to call curator for every
   `concepts_touched` slug (creates new OR appends to existing).
3. `bench_grade.py` L1.5 layer now validates the canonical shape:
   `## Contributions by source` exists, one `### <slug>` per
   `touched_by` entry, frontmatter has `first_introduced_in`.
4. D8 pilot v1 retroactively flagged: 84 L1.5 violations
   (vs Opus baseline: 0). v2 rerun expected to clear them.

**`[≈ MM:SS]` timestamps — kept as enrichment.** They were the one
genuine addition. The canonical template mentions `[mm:ss]` format on
the See-link bullet; we adopt that format. `[≈ MM:SS]` was my
notational variant — folded back to `[mm:ss]` to match canonical.

**Lesson:** before writing a "new" template, exhaustively grep for
existing ones in the source-of-truth repo. Spec drift is much cheaper
to prevent than to fix.

---

**Below is the original (now obsolete) v3 specification, kept for
audit trail. Do NOT use.** All references in run-d8-pilot.py and
step7_orchestrator.py have been updated to canonical skill v2.

---

---

## Template

```markdown
---
slug: <kebab-case-id>
introduced_in: <full source slug, exact match to a source.md slug>
touched_by:
  - <full source slug 1>
  - <full source slug 2>
  - <full source slug 3>
related:
  - <related-concept-slug-1>
  - <related-concept-slug-2>
---

# <Russian title>

## Definition

<2-3 paragraphs grounded in the lecture content of `introduced_in`.
Quote the speaker's framing verbatim with «...» where relevant. The
definition is the speaker's framing, not Wikipedia's.>

## Touched in sources

For EACH source listed in `touched_by`, EXACTLY ONE entry, in the
same order:

- [<short source label>](../sources/<full source slug>.md)
  <1-3 sentence excerpt of what THIS source says about THIS concept,
  not a general source summary. Quote speaker's words with «...» if
  available. Include claim numbers if relevant: «(Claims #3, #7)».>
  [≈ MM:SS]

## See also

- <related-concept-slug-1> — <one-line of why related>
- <related-concept-slug-2> — <one-line of why related>
```

---

## Field-by-field rules

### Frontmatter

- `slug` — kebab-case English (or transliterated Russian) identifier.
  Filename MUST be exactly `<slug>.md`.
- `introduced_in` — exactly one source slug, matching a real
  `wiki/data/sources/<slug>.md` file. This is the source that first
  defines the concept.
- `touched_by` — YAML list of source slugs. MUST include
  `introduced_in` as the first entry. Sources are listed in **order
  of appearance** (curriculum order, derived from numeric source
  prefix `000`, `001`, ...).
- `related` — 2-5 other concept slugs. NOT a citation list — these are
  intellectually-related concepts the reader should explore next.
  Avoid bidirectional explosion (don't list every concept-co-occurrence,
  pick the 2-5 most informative).

### `## Definition`

- 2-3 paragraphs.
- Grounded in lecture transcript of `introduced_in`. Don't paraphrase
  Wikipedia.
- Quote speaker's framings: «термин X означает Y».
- No bullets in this section — it's prose.

### `## Touched in sources` — THE NEW SECTION

This is the navigation backbone. It MUST exist whenever
`len(touched_by) ≥ 2`. If only `introduced_in` itself is listed
(single-source concept), still emit this section with the single entry,
for consistency.

**Per-entry structure (mandatory):**

1. Bullet starts with markdown link to source.md:
   `[<short label>](../sources/<full source slug>.md)`
   - `<short label>` = last path component of source slug, truncated
     to ~60 chars (e.g. `005/002 Социальный успех`).
   - The link target is **relative path** from the concept file
     location (`wiki/data/concepts/<slug>.md`) to the source file
     (`wiki/data/sources/<source-slug>.md`). Since both share parent
     `wiki/data/`, the prefix is always `../sources/`.

2. **Excerpt body**, 1-3 sentences:
   - Describes what THIS source said about THIS concept specifically.
   - NOT a general summary of the source.
   - Cite claim numbers if relevant: `(Claims #3, #7)`.
   - Quote speaker's words with «...» where they directly addressed
     the concept.
   - Minimum 30 characters; maximum ~400 characters.

3. **Timestamp** (optional but recommended): `[≈ MM:SS]` at end of
   excerpt.
   - Derived from whisper `segments` matching the concept's first
     mention in the source's transcript.
   - Format: `[≈ M:SS]` if under 10 min, `[≈ MM:SS]` otherwise.
   - Use `≈` (approximate) — segment boundaries don't align exactly
     with concept mentions.

### `## See also`

- 2-5 bullets, one per related concept.
- Each bullet: `<slug> — <one-line of why related>`.
- The "why" should distinguish between siblings, parents, and
  applications.

---

## Example (Cyrillic, real-world)

```markdown
---
slug: chimeras
introduced_in: Психолог-консультант/005 Природа внутренних конфликтов. Базовые психологические потребности/000 Вводная лекция. Базовые биологические потребности в концептуальной модели системной поведенческой психотерапии
touched_by:
  - Психолог-консультант/005 Природа внутренних конфликтов. Базовые психологические потребности/000 Вводная лекция. Базовые биологические потребности в концептуальной модели системной поведенческой психотерапии
  - Психолог-консультант/005 Природа внутренних конфликтов. Базовые психологические потребности/002 1.1 Социальный успех. Почему мы не можем жить без других но и с ними тяжело
  - Психолог-консультант/005 Природа внутренних конфликтов. Базовые психологические потребности/004 1.3 Социальный успех. Почему мы не можем жить без других но и с ними тяжело
related:
  - internal-conflict
  - dual-vector-model
  - neurotic-styles
---

# Химеры

## Definition

Курпатов вводит «химеры» как сложные подсознательные образования, которые
возникают при хроническом конфликте противоположных векторов внутри
одного инстинкта или между инстинктами. «Химеры — это сложные
образования, которые сбивают сознание с толку и приводят к неврозам».

В отличие от «чистого» инстинктивного импульса, химера — гибридная
структура: импульс самосохранения, переплетённый с импульсом социального
одобрения и подавленным сексуальным компонентом, например. Сознание не
видит исходные векторы, видит только результирующий «странный» симптом.

## Touched in sources

- [005/000 Вводная лекция](../sources/Психолог-консультант/005 Природа внутренних конфликтов. Базовые психологические потребности/000 Вводная лекция. Базовые биологические потребности в концептуальной модели системной поведенческой психотерапии.md)
  Курпатов впервые вводит концепт химер в контексте трёхэтажной модели
  Маклина: «бессознательная лимбическая система генерирует напряжение,
  а сознание неверно его интерпретирует» (Claims #4, #11). Химера = тот
  результат неверной интерпретации. [≈ 18:42]

- [005/002 1.1 Социальный успех](../sources/Психолог-консультант/005 Природа внутренних конфликтов. Базовые психологические потребности/002 1.1 Социальный успех. Почему мы не можем жить без других но и с ними тяжело.md)
  Расширяет концепт на социальную сферу: химеры объясняют, почему люди
  «застревают» в дисфункциональных социальных паттернах (Claims #6, #8).
  Социальная химера = страх отвержения, переплетённый с потребностью в
  иерархическом доминировании. [≈ 03:15]

- [005/004 1.3 Социальный успех](../sources/Психолог-консультант/005 Природа внутренних конфликтов. Базовые психологические потребности/004 1.3 Социальный успех. Почему мы не можем жить без других но и с ними тяжело.md)
  Применяет концепт химер к анализу невротических стилей жизни Адлера:
  стиль «жалующегося» — это химера потребности в признании × подавленной
  агрессии (Claims #2). [≈ 22:00]

## See also

- internal-conflict — фундамент: химеры рождаются из внутреннего
  конфликта противоположных векторов
- dual-vector-model — механика двойного вектора, питающего химеру
- neurotic-styles — клиническое проявление хронических химер по Адлеру
```

---

## Validation (bench_grade.py L1.5)

New rule layer between L1 (frontmatter present) and L2 (claims wellformed):

```python
def validate_concept(concept_path: Path) -> list[str]:
    """Return list of violations; empty list = OK."""
    violations = []
    text = concept_path.read_text()

    # L1.5.a — frontmatter has touched_by
    fm = parse_frontmatter(text)
    touched_by = fm.get("touched_by", [])
    if not touched_by:
        violations.append("touched_by missing or empty")
        return violations

    # L1.5.b — ## Touched in sources section exists
    if "## Touched in sources" not in text:
        violations.append("## Touched in sources section missing")
        return violations

    section = extract_section(text, "## Touched in sources")
    bullets = re.findall(r"^- \[([^\]]+)\]\((\.\./sources/[^)]+)\)\n\s+(.+?)(?=\n- |\n##|\Z)",
                         section, re.MULTILINE | re.DOTALL)

    # L1.5.c — one bullet per touched_by entry
    if len(bullets) < len(touched_by):
        violations.append(
            f"## Touched in sources has {len(bullets)} entries; "
            f"touched_by lists {len(touched_by)} sources"
        )

    # L1.5.d — each bullet has substantive excerpt
    for label, link, excerpt in bullets:
        excerpt_clean = re.sub(r"\[≈[^\]]+\]", "", excerpt).strip()
        if len(excerpt_clean) < 30:
            violations.append(f"excerpt for '{label}' too short ({len(excerpt_clean)} chars)")

    # L1.5.e — link targets are valid (file exists)
    for label, link, excerpt in bullets:
        target = concept_path.parent / link
        if not target.exists():
            violations.append(f"link target missing: {link}")

    return violations
```

---

## Migration of existing concepts

Existing concept files (D7, D7-rev2, D7-rev3, D7-rev4-v2 baselines) lack
the `## Touched in sources` section. Migration script:

```bash
python3 wiki/skills/benchmark/scripts/migrate_concepts_v3.py
```

Walks `wiki/data/concepts/*.md`, for each concept:
1. Reads `touched_by` from frontmatter.
2. For each source slug in `touched_by`, reads the corresponding
   `wiki/data/sources/<slug>.md`.
3. Extracts a 1-3 sentence excerpt mentioning the concept slug (or its
   Russian title) — heuristic: find paragraphs in `## Лекция` containing
   the concept slug as inline link, take 1-2 sentences around it.
4. (D8 enhancement) Compute embedding similarity to find the best
   excerpt automatically.
5. Re-emit `## Touched in sources` section before `## See also`.

Idempotent: if section exists, regenerate it (don't append duplicates).

---

## Authoring responsibility

- **`source-author`** (in source's processing): collects per-claim
  segment timestamps from whisper segments. Stores them alongside
  claims in source.md (e.g. as `<!-- segment: 1842 -->` HTML comment
  in `## Claims` markup).
- **`concept-curator`** (in concept creation/update): given concept
  slug, definition, source slug, and lecture excerpt, produces:
  - `## Definition` paragraph
  - `## Touched in sources` entry for this source (only one per call;
    multi-source concepts accumulate entries from successive curator
    calls)
  - `## See also` entries (proposed by source-author, refined by
    curator)

---

## Open questions

1. **Extracting clean excerpts is hard for 27B models.** Curator
   needs to find "the paragraph in source.md that says something
   substantive about THIS concept" — currently sources have inline
   concept-links, so curator can grep for them. Validate on synth
   that this approach yields excerpts above 30-char threshold.

2. **Timestamp drift.** Whisper segments are 5-30s long; the concept
   may be discussed across multiple segments. Default: use the
   **first** segment containing the concept's keyword. Refinement
   path (D9+): use embedding similarity over segments to find the
   "most central" segment for the concept.

3. **Cross-module navigation.** When `touched_by` spans modules, the
   relative path `../sources/` still works since all sources live
   under `wiki/data/sources/<course>/<module>/<source>.md`. No
   special handling needed.

4. **Concept rename.** If a concept's slug changes (D8 dedup may
   merge `social-instinct` → `social-need`), all `## Touched in sources`
   sections in OTHER concept files referencing it stay valid via
   markdown links to `source.md` (not via concept slug). Concept
   rename only affects `related:` lists and `concept-index.json`.
