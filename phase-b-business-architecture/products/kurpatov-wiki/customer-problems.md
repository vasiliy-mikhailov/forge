# Kurpatov-wiki — customer problems (CI-4)

Per [`/phase-requirements-management/wiki-customer-interview.md`](../../../phase-requirements-management/wiki-customer-interview.md)
CI-4: top-N named problems extracted from
[`customer-observations.md`](customer-observations.md)
(forge schema stub) + private full file at
`kurpatov-wiki-wiki/metadata/customer-observations.md`. This
file is the **schema-conformant** deliverable for CI-5 R-NN
row emission.

Per [ADR 0018](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md)
no Курпатов excerpts in this file; problem definitions are
expressed as wiki-side defects, not lecture-side content.

## Cross-link

- Schema stub (this directory): [`customer-observations.md`](customer-observations.md).
- Private full file: `kurpatov-wiki-wiki/metadata/customer-observations.md`.
- Cycle definition: [`../../../phase-requirements-management/wiki-customer-interview.md`](../../../phase-requirements-management/wiki-customer-interview.md).
- Driver ADR: [`../../../phase-preliminary/adr/0016-wiki-customers-as-roles.md`](../../../phase-preliminary/adr/0016-wiki-customers-as-roles.md).
- Skip-share metric: [`../../../phase-preliminary/adr/0026-per-persona-cumulative-knowledge-and-skip-share.md`](../../../phase-preliminary/adr/0026-per-persona-cumulative-knowledge-and-skip-share.md).

## Severity coding

- **CRITICAL** — blocking-severity for ≥ 2 personas; affects
  any reading-mode use of the wiki; needs R-NN row at OPEN
  status (architect-approved) before next K-experiment.
- **HIGH** — blocking-severity for 1 persona OR moderate for
  ≥ 3; needs R-NN row at PROPOSED status; review with
  architect.
- **MEDIUM** — moderate-severity for ≥ 2 personas, no
  blocking; backlog candidate.

## Affected-persona shorthand

M = academic-researcher; A = entry-level-student; L = lay-curious-reader;
T = time-poor-reader; W = working-psychologist.

## Top problems

### P-1 — Wiki pipeline emits duplicate / empty / fragmented stems that consume reader time

- **Severity**: CRITICAL
- **Affected personas**: M, A, L, T, W (5/5)
- **Observation evidence**: CO-01-X (duplicate-pair), CO-02-X (empty-stub), CO-03-X (whisper-VAD degradation), CO-04-X (missing attachments), CO-05-X (audio-recap-of-text-pair).
- **Evidence count**: 5 cross-persona pipeline observations; ≥ 12 distinct corpus-level pipeline-bug instances per T persona tally.
- **Recommended-action class**: pipeline hardening (sha256 dedup, empty-stub detection, VAD-degradation detector, attachment extraction, audio↔text dedup with auto-summary).
- **Reading-cost** (per T persona): «pipeline costs reader ~30% of budget»; per M persona: 4 corpus instances of pipeline-imperfection raise reproducibility chapter-finding to load-bearing.
- **Closure**: re-walk CI-1..5 (CI-7) post-pipeline-fix; expected per-persona pain count drop on lectures 027, 035, 037, 034b — drop should land before next module's CI cycle.

### P-2 — Names / authors / terms are introduced without one-line context anchor

- **Severity**: CRITICAL
- **Affected personas**: M, A, L, T, W (5/5)
- **Observation evidence**: CO-06-X (names-without-context), CO-08-X (forward/backward-refs), CO-17-X (Курпатов-own-terms), with CO-19-M variant for academic primary-source citation depth and CO-21-A variant for linear-builder.
- **Evidence count**: ≥ 15 named authors per A persona's enumeration; ~220 open primary-source citations per M persona; corpus-wide pattern.
- **Recommended-action class**: concept-graph quality lift — at first mention of any author, inline one-line anchor (name / years / nationality / what known for) embedded by the source-author or concept-curator; per-author concept.md node with citation list; glossary-of-names page on wiki home; cross-link forward/backward references.
- **Closure**: post-fix re-walk shows A persona's «name without context» complaint count drop ≥ 50%; M persona's «open citation» count drops below 100.

### P-3 — Density spikes (5+ concepts / minute) and missing TL;DR exit summaries make scanning impossible

- **Severity**: CRITICAL
- **Affected personas**: A, L, T (3/5 blocking) + M, W (5/5 moderate)
- **Observation evidence**: CO-07-X (density spikes), CO-09-X (filler density), CO-10-X (TL;DR absence), CO-27-T (buried-lede pattern).
- **Evidence count**: 6 corpus instances of buried-lede per T; «5+ concepts/min» pattern in lecture 011, 020, 026/4.3 etc.
- **Recommended-action class**: source-md authoring requirement — lead with TL;DR (one paragraph, ≤ 100 words); close with `## Главное` (≤ 3 bullets); enforce density budget (≤ 3 new concepts per audio-minute introduction-rate); K2 Air-strip already in flight delivers ~part of this.
- **Closure**: T persona's per-lecture would_skip_share drops from 0.64 → ≤ 0.40 corpus-mean post-fix; A persona's «had to rewind N times» complaint disappears.

### P-4 — Filler density and audio length without chapter markers makes the corpus unreadable for short-attention reading modes

- **Severity**: HIGH
- **Affected personas**: A, L, T (3/5 blocking)
- **Observation evidence**: CO-09-X (filler density), CO-13-X (long-audio without chapter markers), CO-24-L (phone-burst incompatibility).
- **Evidence count**: every spoken lecture; 4–6 audios > 30 min without chapters.
- **Recommended-action class**: K2 compact-restore (in flight — `R-B-compact-restore`) plus auto-generated H3 chapter markers from segment-density / topic-shift; per-persona compressed view with would_skip_share threshold drop (per ADR 0026 § 4 — feeds K3 experiment).
- **Closure**: lay-curious would_skip_share drops 0.57 → ≤ 0.30; T's compression ratio against text-track stable at 3-10×.

### P-5 — Genre / format mixing (lecture / methodology / case / session / interstitial) without surface markers

- **Severity**: HIGH
- **Affected personas**: A, L, T (3/5 moderate); reinforced by A and L verbatim
- **Observation evidence**: CO-11-X (genre mixing), CO-22-A (format glossary missing), CO-29-T (workbook unmarked).
- **Evidence count**: 7 workbook instances per T; full-corpus pattern.
- **Recommended-action class**: frontmatter `format:` field (lecture / methodology / case / session / interstitial / workbook); navigation surfaces it; nav badge per format.
- **Closure**: per-persona nav-error rate (clicks-into-wrong-format) drops to 0; A persona's «no genre frame» complaint disappears.

### P-6 — Factual-error candidates accumulate at audio-channel rate; outdated frameworks rendered as current science

- **Severity**: CRITICAL
- **Affected personas**: M, W (2/5 blocking)
- **Observation evidence**: CO-14-X (factual-error candidates ~63% per-lecture rate in biographical / theoretical / empirical territory), CO-15-X (post-Freudian-evolution void), CO-33-W (catharsis-as-fact, Penisneid-as-causal, sexual-orientation-pathologisation framings rendered as current science).
- **Evidence count**: 27 verified M-persona-candidates; 0 systematic treatment of post-1923 evolution per W persona.
- **Recommended-action class**: fact-check pass at concept-curator level for biographical / theoretical / empirical claims; correction-with-attribution in concept.md graph; «mainstream-status: outdated / contested / superseded-by» frontmatter per concept; flag-on-uncertainty annotation for audio-blocked claims.
- **Closure**: M persona's verified-error count drops on re-walk; «check needed» annotation count converges as fact-check pass progresses.

### P-7 — Ethics-violation modeling at pedagogical-instrumentation level (15 ethics-action issues; pedagogy/practice mismatch)

- **Severity**: CRITICAL
- **Affected personas**: W (1/5 blocking, with Marina-corroboration via CO-16-X)
- **Observation evidence**: CO-16-X (cross-persona — pedagogical-instrumentation-without-trauma-informed-care: 15+ corpus iterations per W and 15+ per M); CO-30-W (15 issues persona-specific tally); CO-31-W (pedagogy/practice mismatch — L42 live demo demonstrates coaching, not psychoanalysis).
- **Evidence count**: 15 ethics-action-level issues, 1 central pedagogy/practice mismatch evidence point.
- **Recommended-action class**: ethics-overlay layer in wiki (15-issue inventory + safety scaffolding hint + opt-out language + crisis-helpline pointer + qualified-clinician disclaimers); claim/practice comparative panel («course teaches X / lecturer practices Y»); honest re-labeling of demo-lectures (coaching vs psychotherapy); negative-example tagging for supervision-teaching.
- **Closure**: ethics overlay landed as wiki concept; W persona's «iatrogenic risk» complaint count drops to 0 with explicit disclaimer-coverage; clinician-trainee can read corpus without modeling un-trauma-informed practice.

### P-8 — Curriculum gaps in core areas (defenses; modern relational; trauma research; EBP; IPV; informed consent / formulation modeling) — 0 systematic treatment

- **Severity**: HIGH
- **Affected personas**: W (1/5 blocking)
- **Observation evidence**: CO-32-W (~20 curriculum gap categories enumerated).
- **Evidence count**: 20+ named gap categories.
- **Recommended-action class**: compensatory reading-list overlay in wiki (~150 references per W persona's list — full reference enumeration in private observations file); per-concept «mainstream-status + alternatives» frontmatter.
- **Closure**: every concept.md node with «outdated / superseded» status carries an alternative reference; W can rely on the wiki for «what is current» reading without external deep dive.

### P-9 — Russian-language psychoanalytic-literary-reading genealogy attribution void

- **Severity**: HIGH
- **Affected personas**: M (1/5 blocking)
- **Observation evidence**: CO-20-M.
- **Evidence count**: 3 corpus instances saturating across L29 + L34 + L40.
- **Recommended-action class**: explicit chapter / sidebar in wiki on the Russian-language psychoanalytic-literary-reading tradition genealogy with primary-source citations (full reference list lives in private observations file); current-author revival positioned in tradition.
- **Closure**: M persona's chapter §3.4 gets a citation-anchored genealogy block; her open-citation count for this thread → 0.

### P-10 — Per-persona reading guides absent (case-first vs theory-first ordering; Tier-1/Tier-2/Tier-3 digests)

- **Severity**: MEDIUM
- **Affected personas**: L, T (2/5 moderate)
- **Observation evidence**: CO-18-X (case-first vs theory-first preferred order), CO-26-L (case-demo lecture should be earlier), and T persona's 30-min digest sketch (Tier-1 + Tier-2 + Tier-3 ≈ 30 min for ~80% corpus value).
- **Evidence count**: 2 personas explicitly request guides; both produce concrete sketches.
- **Recommended-action class**: per-persona reading-guide page (one per persona); social-proof navigation («readers like you started with …»); driven by `customer:<persona>` tag on individual lectures via the catalog R-NN traceability.
- **Closure**: each persona's chain summary recommendation is operationalised as a wiki «reader path»; user-test (next CI cycle) shows persona's chosen path matches the recommendation.

## Recommended-action mapping (problem → R-NN proposal)

This table feeds directly into CI-5. Full draft trajectory rows
in `CI-5-rnn-draft.md` (private — for architect review before
catalog commit).

| Problem | Proposed R-NN slug                  | Quality dim                           | Source cell                             |
|---|---|---|---|
| P-1     | `R-B-pipeline-hygiene-pass`         | Pipeline correctness / Dedup / Reproducibility | customer:M, customer:A, customer:L, customer:T, customer:W + A: TTS |
| P-2     | `R-B-author-name-anchors`           | Concept-graph quality                 | customer:M, customer:A, customer:L, customer:T, customer:W + A: TTS |
| P-3     | `R-B-tldr-and-density-budget`       | Reading speed / Concept-graph quality | customer:A, customer:L, customer:T + A: TTS |
| P-4     | `R-B-chapter-markers-and-air-strip` | Reading speed / Voice preservation    | customer:A, customer:L, customer:T + A: TTS |
| P-5     | `R-B-format-frontmatter-and-nav`    | Voice preservation / Reading speed    | customer:A, customer:L, customer:T |
| P-6     | `R-B-factcheck-pass-and-mainstream-status` | Fact-check coverage              | customer:M, customer:W |
| P-7     | `R-B-ethics-overlay-and-claim-practice-panel` | Fact-check / Reproducibility   | customer:W (+ M corroborates) + A: PTS (clinician-segment) |
| P-8     | `R-B-compensatory-reading-list`     | Concept-graph quality                 | customer:W |
| P-9     | `R-B-russian-genealogy-chapter`     | Fact-check / Concept-graph quality    | customer:M |
| P-10    | `R-B-per-persona-reading-guides`    | Voice preservation / Reading speed    | customer:L, customer:T (extensible) |

## Notes for architect

- **CI-4 ground-truth re-listen pending**. Per the cycle
  spec the Wiki PM should re-listen to the highest-stakes
  lectures before merging substance findings. CO-31-W (the
  «pedagogy/practice mismatch — L42 live demo is coaching,
  not psychoanalysis» finding) is the most consequential
  single-persona substance observation in the corpus and
  warrants explicit re-listen before any R-NN around P-7
  goes to OPEN. Same for the factual-error candidates in P-6
  (especially the L40 1927-cluster + L38 Russian-2002
  empirical claim — both whisper-rendering uncertain).
- **Privacy boundary**. P-7's full evidence (verbatim ethics
  failures with seg-level references) lives in the private
  observations file; this forge-side problem statement names
  the issue class without citing the lecture material.
- **Trajectory model compatibility**. All 10 problems map to
  Phase-B capability quality dimensions; none requires a new
  Phase-A goal. P-7 has cross-Phase implication (PTS is
  affected for the W segment specifically, but Phase A's PTS
  is currently a placeholder per `R-A-PTS`).
- **Single-persona problems** (P-7 W-only, P-8 W-only,
  P-9 M-only) are PROPOSED-PERSONA-SPECIFIC per CI-5 rule;
  architect decides whether the wiki ships fixes that serve
  one segment or whether the W/M segments are out-of-scope
  for the current product line iteration.

## Closure measurement

Per ADR 0016 § Steps CI-7: each P-N closes when its driving
observation count drops to 0 across all personas that
originally voted on it (not just a subset). Re-walk schedule
matches K-experiment cadence (post-K2 already due; K3
compress-by-redundancy is the natural P-3 + P-4 closure
attempt).
