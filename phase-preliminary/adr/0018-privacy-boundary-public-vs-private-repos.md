# ADR 0018 — Privacy boundary: lecture excerpts live in private repos, not in public forge

## Status

Accepted (2026-05-02). Active.

## Measurable motivation chain
Per [P7](../architecture-principles.md):

- **Driver**: forge is a public GitHub repo
  (`vasiliy-mikhailov/forge`); the Курпатов lecture corpus
  is the architect's commercial IP and lives in private repos
  (`vasiliy-mikhailov/kurpatov-wiki-raw` for raw transcripts (immutable),
  `vasiliy-mikhailov/kurpatov-wiki-wiki` for the compiled
  wiki). Pre-this-ADR, forge contained
  `phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`
  with **30 Cyrillic verbatim quotes** from Kurpatov lectures —
  IP leakage to public repo.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: every artifact containing Kurpatov-content
  excerpts (verbatims, paraphrases, segment text) lives in
  the private `kurpatov-wiki-wiki` repo (alongside the curated source.md + concept.md outputs); forge contains only
  the **architecture metamodel** (schema, structure,
  cross-references, predicates).
- **Measurement source**: audit-predicate: P25 (queued — Cyrillic-excerpt scan)
- **Contribution**: ADR enforces a discipline that prevents one bug class; contributes to Quality KR via reduced incidents.

## Context

Forge today is the Architect's home-lab architecture
metamodel — a public reference for "how to do
TOGAF + ArchiMate + RLVR for an LLM-agent-driven home-lab".
The Kurpatov wiki is one of forge's **products**; its content
is commercial. The public/private split mirrors the standard
"open-source the framework, keep the data private":

- forge (PUBLIC): TOGAF/ArchiMate metamodel, Roles, Predicates,
  Audits, ADRs, Test runners, Capability + Product structure.
- kurpatov-wiki-raw (PRIVATE): raw.json transcripts produced
  by faster-whisper from the audio. IMMUTABLE — machine-
  generated; not a curation target.
- kurpatov-wiki-wiki (PRIVATE): compiled source.md +
  concept.md graph PLUS curated metadata (corpus observations
  + per-persona pain ledgers + any other artifact containing
  lecture content). The Wiki PM's S1+S2 corpus walk + the
  CI-1..7 customer-interview cycle both write here.

Pre-2026-05-02 forge violated the boundary in three places:

1. `phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`
   — 30 OBS-X-NNN entries with verbatim Cyrillic quotes
   (e.g. `"Стресс — это, если опираться на определение,
   которое дал ему автор теории Ганс Селье..."`).
2. `phase-b-business-architecture/products/kurpatov-wiki/customer-pains/`
   — 5 empty directories created in [ADR 0016](0016-wiki-customers-as-roles.md)
   for ledger storage; future ledgers would have contained
   excerpts.
3. `phase-c-…/wiki-bench/tests/synthetic/fixtures/k2/lecture_A_synth.json`
   — synthetic Cyrillic content the architect *authored*
   (not real Kurpatov). NOT a violation per se (it's
   synthetic), but the line between synth and real must
   stay sharp.

This ADR fixes (1) + (2); confirms (3) is OK if the synth
content stays clearly synthetic.

## Decision

### 1. Public/private boundary

The boundary is enforced by **repo membership**:

- forge (PUBLIC) MUST NOT contain:
  - Verbatim Cyrillic text from Kurpatov audio / transcripts /
    slides.
  - Paraphrases of Kurpatov claims that would let a reader
    reconstruct material content.
  - Pain ledger entries citing specific lecture passages.
  - **Customer assessments of the wiki product** (extended
    2026-05-02 per architect call): per-lecture pain ledgers,
    cumulative `__knowledge.md` files, CI-3 customer-observation
    content (severity tallies, distribution-character descriptions,
    bucket-content enumerations with examples), CI-4 named
    problem statements (P-N with severity / evidence / recommended
    action), would_skip_share aggregates by lecture / persona,
    factual-error candidate logs, ethics-violation tallies,
    pedagogy/practice mismatch findings. These constitute critique
    of a commercial product (Kurpatov's course); they are
    customer-derived assessments, not architecture metamodel.
- forge (PUBLIC) MAY contain:
  - Schema declarations (observation IDs, bucket NAMES (without
    in-bucket-content examples that paraphrase corpus),
    dimension catalog, persona definitions, ID conventions,
    persona-letter mappings).
  - Cross-reference paths to private content.
  - Walk metadata (date, scope, methodology used) — but NOT
    counts of pains / observations / verdicts.
  - R-NN trajectory rows (R-NN names + `customer:<persona>`
    Source-cell tags + Quality dimension cells; Level 1 / Level 2
    cells must be sanitised — describe action class, not
    assessment evidence).
  - Synthetic content the architect explicitly authored
    (clearly marked as synth — `lecture_A_synth.json`,
    `synth-corpus-observations.md`).

### 2. corpus-observations.md split

The file moves in two directions:

- **forge (public)**:
  `phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`
  retained as a **schema-only stub**. Lists OBS IDs (OBS-X-NNN
  format), source-letter mapping (A → 000 Знакомство, B → 002
  Вводная лекция, …), bucket / dimension catalog, count
  totals. NO verbatim quotes. Cross-links to the private
  full file.
- **kurpatov-wiki-wiki (private)**: NEW
  `metadata/corpus-observations.md` carries the full content
  including Cyrillic verbatims + per-OBS classifications.
  Mirrored from forge's pre-ADR-0018 file. Sits in the same
  repo as the curated source.md / concept.md outputs the
  observations describe.

### 3. Customer pain ledger location

ADR 0016 said pain ledgers live at
`phase-b-business-architecture/products/kurpatov-wiki/customer-pains/<persona>/<lecture-stem>.md`
(in forge). **Corrected**: ledgers live at
`kurpatov-wiki-wiki/metadata/customer-pains/<persona>/<lecture-stem>.md`
(in private).

The forge `customer-pains/` directories (5, all empty) are
deleted per delete-on-promotion + privacy.

### 4. wiki-customer-interview.md updated

CI-2 (activate persona) writes to the private path. CI-3
(cross-tabulate) reads the private path; the cross-tab table
itself can live in private OR forge depending on whether it
contains excerpts. **Default: private.**

CI-5 emission of R-NN rows still goes into forge's
`catalog.md` (R-NN names + Source cells are not excerpts).

### 5. measure-corpus-recall.py default path

The `--observations` CLI default points at the private
`kurpatov-wiki-wiki/metadata/corpus-observations.md` (via a
`_find_repo` lookup). Forge stub is no longer the default
(would yield 0 hits since stub has no verbatims).

### 6. Synthetic content stays in forge clearly marked

`lecture_A_synth.json`, `synth-corpus-observations.md`,
`bloated-fixture.md`, and any future synth fixtures may live
in forge IF:
- File name contains `synth` OR `_template` OR `_fixture` OR
  is under `/tests/synthetic/fixtures/`.
- Content is the architect's own authoring (not paraphrased
  from real corpus).

### 7. customer-observations.md and customer-problems.md split (NEW 2026-05-02)

Same pattern as corpus-observations.md (per § Decision 2):

- **forge (public)**:
  `phase-b-business-architecture/products/kurpatov-wiki/customer-observations.md`
  retained as a **schema-only stub**: persona-letter mapping
  (M/A/L/T/W → slugs), CO-NN ID convention, bucket-NAMES catalog
  (Pipeline / Form / Concept / Substance) without in-bucket-content
  examples, quality-dimension cross-references. NO observation
  counts (those imply pain volume = assessment). NO skip-share
  aggregates. NO bucket-content enumerations citing specific
  finding classes (e.g. "factual-error candidates").

- **forge (public)**:
  `phase-b-business-architecture/products/kurpatov-wiki/customer-problems.md`
  retained as a **schema-only stub**: severity-coding table
  (CRITICAL / HIGH / MEDIUM definitions), affected-persona
  shorthand, recommended-action mapping schema. NO P-N problem
  statements. NO problem-content. Cross-link to private full file.

- **kurpatov-wiki-wiki (private)**: NEW
  `metadata/customer-observations.md` (already landed in CI-3) and
  NEW `metadata/customer-problems.md` carry the full assessment
  content — per-CO observation classifications + per-lecture
  pain references + P-N problem statements + severity assignments
  + evidence-by-CO-NN + closure-measurement specifics.

CI-5 R-NN trajectory rows in forge `catalog.md` MUST cite CO-NN
and P-N IDs (which resolve to private full content) rather than
inline assessment text in their Level 1 / Level 2 cells.

## Consequences

- **Plus**: public/private IP boundary clear. Future contributors
  to forge (or LLM agents loading forge as context) cannot
  inadvertently leak Kurpatov content.
- **Plus**: private repo holds the wiki-content evidence
  alongside the raw transcripts that produced it — co-located
  artifacts, easier to walk together.
- **Minus**: cross-repo coordination (a forge audit walking
  P21/P22 etc. needs to know about the private repo's
  metadata). Mitigated by: the audit reads private content
  read-only via the local mount; no audit findings about
  private content are emitted to forge.
- **Minus**: contributors to forge cannot reproduce the
  audit's Substance/Form/Air signal end-to-end without
  access to the private corpus. This is the correct trade-off:
  the methodology is public, the data isn't.

## Invariants

- A new artifact landing in forge that contains Cyrillic
  Kurpatov-corpus excerpts (or paraphrases material to reproduce
  content) is a P25 FAIL on the next audit walk (P25 to be added
  in audit-2026-05-01w; this ADR's first follow-up).
- The boundary is enforced by **content**, not by file path —
  any forge file (any phase) is in scope for the rule.
- Synthetic content in forge MUST carry a `synth` / `fixture` /
  `_template` marker in its name OR live under
  `/tests/synthetic/fixtures/`.
- The `_find_repo` helper in scripts/test-runners locates
  `kurpatov-wiki-raw` and `kurpatov-wiki-wiki` from sibling
  paths; CI runners that need lecture content read-only-mount
  the private repo.

## Alternatives considered

- **Keep corpus-observations.md in forge but redact verbatims
  inline.** Considered. Rejected: the file's value IS the
  verbatims (per S1+S2 of the Wiki PM cycle); a redacted
  version is useless. Splitting (schema stub in public, full
  in private) preserves both audiences.
- **Move ALL `phase-b-business-architecture/products/kurpatov-wiki/`
  to private.** Considered. Rejected: the per-product file
  declarations are part of the public Capability decomposition
  (forge demonstrates "how to model a wiki product"); they're
  schema, not content. Stays in forge.
- **Make forge private too.** Considered. Rejected: forge IS
  the public reference; the home-lab architecture method is
  open by intent (per ADR 0014's adoption of TOGAF/ArchiMate
  as a standards-based public approach).

## Follow-ups

- **P25** in audit-process.md: scan forge md files for Cyrillic
  excerpts (`[А-Яа-яЁё]+` runs ≥ N words long, excluding
  carve-outs for synth fixtures + the ArchiMate vocabulary
  file's spec citations). Default = `WARN` if found; `FAIL`
  if not in carve-out + ≥ 50 words.
- **P25 carve-out list**: synth fixtures (per name pattern);
  ArchiMate spec citation excerpts (in archimate-language.md);
  audit findings citing OBS-X-NNN by ID only (not by verbatim).
- Run a one-time scan of forge for any other Cyrillic excerpts
  beyond the 3 known sources. Audit it out.
- The 5 customer pain ledgers from the upcoming CI cycle (when
  it runs against modules 000+001) land in
  `kurpatov-wiki-wiki/metadata/customer-pains/`. Per ADR 0018.
