# test-wiki-pm — agentic behaviour tests for the Wiki PM role

Behavioural specification for the
[Wiki PM role](../../../phase-b-business-architecture/roles/wiki-pm.md).
Path mirrors the source path of the role (per
[ADR 0013](../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)).

## What an agentic behaviour test is

A test case states **when [condition] then [expected behaviour]**.
The test is the spec — not code. A separate *runner* (manual,
scripted, or LLM-as-judge) executes the case by setting up the
agent, sending the input, and comparing the agent's real output
against the expected result. The runner is a derived mechanism
and lives outside `tests/` (today: `scripts/test-runners/`).

Each case has four sections:

- **Set expected result** — what the agent should produce.
  Defined first.
- **Arrange** — bake in the input data; arrange the agent.
- **Act** — send the input; gather the real result.
- **Assert** — `expected = real`. Verdict: `PASS` / `FAIL` /
  `PENDING`.

Cases are numbered `WP-<NN>`.

## Cases

| ID    | When … then …                                                                                                                                                  | Verdict |
|-------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| WP-01 | When the Wiki PM walks S1+S2, then it produces a corpus-observations file at the canonical path.                                                                | PASS    |
| WP-02 | When the corpus-observations file is produced, then it has Substance / Form / Air buckets each with ≥ 3 observations.                                            | PASS    |
| WP-03 | When the corpus-observations file is produced, then every block-quoted line is a verbatim substring of one of the sampled raw transcripts.                        | PASS    |
| WP-04 | When the corpus-observations file is produced, then it tags ≥ 6 of the 8 capability quality dimensions across observations.                                       | PASS    |
| WP-05 | When the Wiki PM walks S1+S2, then it does not write R-NN rows to the requirements catalog (S7 is out of scope for this run).                                     | PASS    |
| WP-06 | When the Wiki PM walks S1+S2, then it does not modify any wiki-bench file.                                                                                       | PASS    |
| WP-07 | When the Wiki PM is given a "и так далее, и так далее, и так далее" line, then it classifies the line as Air with the Reading-speed dimension.                      | PASS    |
| WP-08 | When the Wiki PM is given a word-doubling line ("эмпатические отношения, эмпатические отношения"), then it classifies it as Air with the Reading-speed dimension.  | PASS    |
| WP-09 | When the Wiki PM is given a self-Q&A scaffolding line ("Все ли это? Тоже далеко не все."), then it classifies it as Air with the Reading-speed dimension.          | PASS    |
| WP-10 | When the Wiki PM is given a definition-with-attribution line, then it classifies it as Substance with the Concept-graph-quality dimension.                          | PASS    |
| WP-11 | When the Wiki PM is given a branded-method self-citation, then it classifies it as Form (or Air on subsequent occurrences) with the Voice-preservation dimension.  | PASS    |
| WP-12 | When the Wiki PM is given a direct-address scenario from raw, then it classifies it as Form with the Voice-preservation dimension.                                  | PASS    |
| WP-13 | When the Wiki PM is given a synonym-chain line, then it tags the chain with the Voice-preservation dimension.                                                       | PASS    |
| WP-14 | When the Wiki PM is given a triple-trail filler, then it tags the line with the Reading-speed dimension.                                                            | PASS    |

WP-01 through WP-06 are mechanically checkable (artefact
inspection); the runner verified them PASS on 2026-04-30.
WP-07 through WP-14 went from PENDING to PASS on 2026-05-01
when the LLM-as-judge harness landed: the Wiki PM role
classified each fixture and the answers were captured in
[`wiki-pm-answers.json`](wiki-pm-answers.json) (the answer
ledger). The runner now scores each case against that ledger
(bucket match + dimension match + rationale keyword match;
3 components, threshold 2, italian-strike 2.0-2.39).

---

## WP-01 When the Wiki PM walks S1+S2, then it produces a corpus-observations file at the canonical path

### Set expected result

A file exists at
`phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`,
non-empty (≥ 30 non-blank lines).

### Arrange

- **Input data.** A pre-selected sample of 5 raw transcripts
  under `kurpatov-wiki-raw/data/Психолог-консультант/` (one
  per format: 88-min spoken intro; written конспект of same;
  module-005 spoken intro; module-005 lecture #1; глубинная
  intro).
- **Agent.** Cowork session loaded with
  [`wiki-pm.md`](../../../phase-b-business-architecture/roles/wiki-pm.md)
  as persona and
  [`wiki-requirements-collection.md`](../../../phase-requirements-management/wiki-requirements-collection.md)
  as activation; only Steps S1 and S2 enabled (S3+ out of scope).

### Act

- Hand the agent the sample raws.
- The agent walks S1 (sample notes) then S2 (bucketed observations).
- The agent writes output to the canonical corpus-observations
  path.

### Assert

- **Expected.** File exists at the path with ≥ 30 non-blank lines.
- **Real.** File presence + line count.
- **Verdict.** PASS if both conditions met.

---

### Reward

**Motivation reference.** Realises the *Outcome* "corpus-observations.md exists as the role's working evidence file" — precondition for every later WP case.

**Score components**:

- C1. File exists at canonical path (1 pt)
- C2. ≥ 30 non-blank lines (1 pt)

**Aggregate.** sum.

**Score range.** 0..2.

**PASS threshold.** 2.

**Italian-strike band.** n/a (both criteria binary).

## WP-02 When the corpus-observations file is produced, then it has Substance / Form / Air buckets each with ≥ 3 observations

### Set expected result

The corpus-observations.md file contains three Markdown level-2
headers — `## Substance`, `## Form`, `## Air` — and each section
has at least 3 observations marked `**OBS-<raw>-NNN**`.

### Arrange

- **Input data.** The corpus-observations.md from WP-01.
- **Agent.** Already produced the file (WP-01 PASS).

### Act

- Read the file.
- Find each bucket header.
- Count `**OBS-` markers within each bucket.

### Assert

- **Expected.** Three buckets present, each with ≥ 3 observations.
- **Real.** Header count + per-bucket observation count.
- **Verdict.** PASS if all conditions met.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's bucketing reaches usable depth" — a bucket with 1 observation is technically present but not substantively useful. ≥ 3 is the floor; richer is better.

**Score components**:

- C1. Substance bucket: 0 if <3 obs, 0.5 if 3-9, 1 if ≥10 (1 pt)
- C2. Form bucket: same scale (1 pt)
- C3. Air bucket: same scale (1 pt)

**Aggregate.** sum.

**Score range.** 0..3.

**PASS threshold.** 1.5.

**Italian-strike band.** 1.5 ≤ score < 2.4 (just-above-floor; reader would call the file shallow).

## WP-03 When the corpus-observations file is produced, then every block-quoted line is a verbatim substring of one of the sampled raw transcripts

### Set expected result

For every block-quoted line (`> …`) in corpus-observations.md
where the quote text is ≥ 8 characters, the quote is found as a
substring of the concatenated whisper-segment text of one of the
sampled raws (after NFC normalisation and whitespace
collapsing).

### Arrange

- **Input data.** The corpus-observations.md + the 5 sampled
  raw transcripts.
- **Agent.** Already produced the file (WP-01 PASS).

### Act

- Extract every block-quoted line ≥ 8 chars.
- For each, search across the concatenated raw transcripts.

### Assert

- **Expected.** Every quote found verbatim.
- **Real.** Per-quote substring search.
- **Verdict.** PASS if zero invented quotes.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role does not invent quotes — provenance is intact." A single fabricated quote breaks reader trust in the entire file.

**Score components**:

- C1. fraction = (verbatim quotes verified) / (total quotes ≥ 8 chars) (1 pt)

**Aggregate.** fraction.

**Score range.** 0..1.

**PASS threshold.** 1.

**Italian-strike band.** n/a — any fabrication is FAIL, not partial credit. Threshold and max are equal.

## WP-04 When the corpus-observations file is produced, then it tags ≥ 6 of the 8 capability quality dimensions across observations

### Set expected result

Across the observation tags `[Dimension]` in corpus-observations.md,
at least 6 of the 8 distinct quality dimensions of the
[Develop wiki product line capability](../../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md)
appear.

### Arrange

- **Input data.** The corpus-observations.md.
- **Agent.** Already produced the file (WP-01 PASS).

### Act

- Extract every `[Dimension]` tag from observation blocks.
- Intersect with the 8-item allow-list (Voice preservation,
  Reading speed, Dedup correctness, Fact-check coverage,
  Concept-graph quality, Reproducibility, Transcription
  accuracy, Requirement traceability).

### Assert

- **Expected.** ≥ 6 distinct dimensions covered.
- **Real.** Distinct-dimension count.
- **Verdict.** PASS if ≥ 6.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's observations cover the breadth of the capability" — a corpus walk that only addresses 3 of 8 quality dimensions misses substantive coverage.

**Score components**:

- C1. fraction = (distinct dimensions tagged) / 8 (1 pt)

**Aggregate.** fraction.

**Score range.** 0..1.

**PASS threshold.** 0.75.

**Italian-strike band.** 0.75 ≤ score < 0.8 (six of eight dimensions exactly; surfaces walks that just barely meet threshold).

## WP-05 When the Wiki PM walks S1+S2, then it does not write R-NN rows to the requirements catalog

### Set expected result

`phase-requirements-management/catalog.md` is unchanged from the
state before the agent's S1+S2 run (S7 — emit R-NN — is out of
scope for this case).

### Arrange

- **Input data.** Pre-run catalog.md state.
- **Agent.** Same as WP-01 (S1+S2 only enabled).

### Act

- Diff catalog.md vs pre-run state.

### Assert

- **Expected.** No diff.
- **Real.** Diff result.
- **Verdict.** PASS if no changes.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role respects its own scope (S7 emits R-NN; S1+S2 do not)." Out-of-scope writes pollute the requirements catalog with un-vetted rows.

**Score components**:

- C1. catalog.md unchanged from pre-run state (1 pt)

**Aggregate.** sum.

**Score range.** 0..1.

**PASS threshold.** 1.

**Italian-strike band.** n/a (binary).

## WP-06 When the Wiki PM walks S1+S2, then it does not modify any wiki-bench file

### Set expected result

No file under
`phase-c-information-systems-architecture/application-architecture/wiki-bench/`
is modified by the agent.

### Arrange

- **Input data.** Pre-run wiki-bench tree state.
- **Agent.** Same as WP-01.

### Act

- Diff the wiki-bench subtree vs pre-run state.

### Assert

- **Expected.** No diff.
- **Real.** Diff result.
- **Verdict.** PASS if no changes.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role does not edit lab code." The role is product-management, not a developer agent; lab edits belong to a different role.

**Score components**:

- C1. wiki-bench subtree unchanged (1 pt)

**Aggregate.** sum.

**Score range.** 0..1.

**PASS threshold.** 1.

**Italian-strike band.** n/a (binary).

## WP-07 When the Wiki PM is given a triple-trail filler, then it classifies the line as Air with the Reading-speed dimension

### Set expected result

The agent's classification of the input contains:

- `bucket = Air`,
- `dimension contains Reading speed`,
- `rationale mentions the trailing "и так далее" chain or the term "filler" / "tail"`.

### Arrange

- **Input data.**

  > переживать, страдать, мучиться и так далее, и так далее, и так далее.

  (Verbatim from `kurpatov-wiki-raw/.../000 Знакомство.../raw.json`.)

- **Agent.** Cowork session loaded with `wiki-pm.md` as persona
  and `wiki-requirements-collection.md` as activation; the
  classification operation is exposed (the agent is asked
  "what bucket does this line belong in").

### Act

- Send the input. Ask: "What bucket does this sentence belong
  in (Substance / Form / Air), and which capability dimension
  does it relate to? One-paragraph rationale."
- Capture the agent's response.

### Assert

- **Expected.** Bucket = Air; dimension contains "Reading
  speed"; rationale references the filler chain.
- **Real.** Parsed agent response.
- **Verdict.** PASS if all three match. PENDING until the
  classification is run.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's classification of a Курпатов line matches the catalogued pattern (Air/Form/Substance with the right dimension)." Sub-Outcome of *Voice preservation* / *Reading speed* (whichever the case targets).

**Score components.** PENDING (no mechanical reward function).

**Aggregate / Score range / PASS threshold / Italian-strike band.**
PENDING (no mechanical reward function). Components require an LLM-as-judge harness: one component per assertion in the case (bucket match, dimension keyword present, rationale keyword present). Each would be 0/1 once wired. The case stays in the
PENDING verdict until the harness lands.

## WP-08 When the Wiki PM is given a word-doubling line, then it classifies it as Air with the Reading-speed dimension

### Set expected result

Bucket = Air; dimension contains "Reading speed"; rationale
mentions "doubling" / "repetition" / "spoken-anchor".

### Arrange

- **Input data.**

  > то есть это эмпатические отношения, эмпатические отношения.

- **Agent.** Same as WP-07.

### Act

- Same as WP-07.

### Assert

- Same shape as WP-07. Verdict: PENDING.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's classification of a Курпатов line matches the catalogued pattern (Air/Form/Substance with the right dimension)." Sub-Outcome of *Voice preservation* / *Reading speed* (whichever the case targets).

**Score components.** PENDING (no mechanical reward function).

**Aggregate / Score range / PASS threshold / Italian-strike band.**
PENDING (no mechanical reward function). Components require an LLM-as-judge harness: one component per assertion in the case (bucket match, dimension keyword present, rationale keyword present). Each would be 0/1 once wired. The case stays in the
PENDING verdict until the harness lands.

## WP-09 When the Wiki PM is given a self-Q&A scaffolding line, then it classifies it as Air with the Reading-speed dimension

### Set expected result

Bucket = Air; dimension contains "Reading speed"; rationale
mentions "rhetorical question" / "self-Q&A" / "lifts the next
claim".

### Arrange

- **Input data.**

  > Все ли это? Тоже далеко не все.

- **Agent.** Same as WP-07.

### Act / Assert

- Same shape as WP-07. Verdict: PENDING.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's classification of a Курпатов line matches the catalogued pattern (Air/Form/Substance with the right dimension)." Sub-Outcome of *Voice preservation* / *Reading speed* (whichever the case targets).

**Score components.** PENDING (no mechanical reward function).

**Aggregate / Score range / PASS threshold / Italian-strike band.**
PENDING (no mechanical reward function). Components require an LLM-as-judge harness: one component per assertion in the case (bucket match, dimension keyword present, rationale keyword present). Each would be 0/1 once wired. The case stays in the
PENDING verdict until the harness lands.

## WP-10 When the Wiki PM is given a definition-with-attribution line, then it classifies it as Substance with the Concept-graph-quality dimension

### Set expected result

Bucket = Substance; dimension contains "Concept-graph quality"
(or "Fact-check coverage"); rationale mentions "attribution" /
"verifiable claim" / "Selye".

### Arrange

- **Input data.**

  > Стресс — это, если опираться на определение, которое дал ему автор теории Ганс Селье, естественная реакция нашей психики и организма на изменения среды.

- **Agent.** Same as WP-07.

### Act / Assert

- Same shape as WP-07. Verdict: PENDING.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's classification of a Курпатов line matches the catalogued pattern (Air/Form/Substance with the right dimension)." Sub-Outcome of *Voice preservation* / *Reading speed* (whichever the case targets).

**Score components.** PENDING (no mechanical reward function).

**Aggregate / Score range / PASS threshold / Italian-strike band.**
PENDING (no mechanical reward function). Components require an LLM-as-judge harness: one component per assertion in the case (bucket match, dimension keyword present, rationale keyword present). Each would be 0/1 once wired. The case stays in the
PENDING verdict until the harness lands.

## WP-11 When the Wiki PM is given a branded-method self-citation, then it classifies it as Form (or Air on subsequent occurrences) with the Voice-preservation dimension

### Set expected result

Bucket = Form (the *first* such citation per source) OR Air
(subsequent occurrences within the same source). Pass on either
since Decision tests are stateless on a single classification
call. Dimension contains "Voice preservation"; rationale mentions
"self-citation" / "branded method" / "СПП authorship".

### Arrange

- **Input data.**

  > Несколько слов скажу, поскольку я сам автор системной поведенческой психотерапии

- **Agent.** Same as WP-07.

### Act / Assert

- Same shape as WP-07. Verdict: PENDING.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's classification of a Курпатов line matches the catalogued pattern (Air/Form/Substance with the right dimension)." Sub-Outcome of *Voice preservation* / *Reading speed* (whichever the case targets).

**Score components.** PENDING (no mechanical reward function).

**Aggregate / Score range / PASS threshold / Italian-strike band.**
PENDING (no mechanical reward function). Components require an LLM-as-judge harness: one component per assertion in the case (bucket match, dimension keyword present, rationale keyword present). Each would be 0/1 once wired. The case stays in the
PENDING verdict until the harness lands.

## WP-12 When the Wiki PM is given a direct-address scenario from raw, then it classifies it as Form with the Voice-preservation dimension

### Set expected result

Bucket = Form; dimension contains "Voice preservation";
rationale mentions "direct address" / "thought experiment" /
"scenario".

### Arrange

- **Input data.**

  > А теперь представьте, что у вас был какой-нибудь близкий друг, с которым вы были в хороших отношениях

- **Agent.** Same as WP-07.

### Act / Assert

- Same shape as WP-07. Verdict: PENDING.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's classification of a Курпатов line matches the catalogued pattern (Air/Form/Substance with the right dimension)." Sub-Outcome of *Voice preservation* / *Reading speed* (whichever the case targets).

**Score components.** PENDING (no mechanical reward function).

**Aggregate / Score range / PASS threshold / Italian-strike band.**
PENDING (no mechanical reward function). Components require an LLM-as-judge harness: one component per assertion in the case (bucket match, dimension keyword present, rationale keyword present). Each would be 0/1 once wired. The case stays in the
PENDING verdict until the harness lands.

## WP-13 When the Wiki PM is given a synonym-chain line, then it tags the chain with the Voice-preservation dimension

### Set expected result

Dimension contains "Voice preservation". Bucket may be Form
(synonym chain identifies a concept) or Air (chain compression
serves Reading speed); pass requires Voice preservation be
among the tags.

### Arrange

- **Input data.**

  > психотерапевтический контакт, установить, иногда это говорят, рапорт, или доверительные отношения с клиентом

- **Agent.** Same as WP-07.

### Act / Assert

- Same shape as WP-07. Verdict: PENDING.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's classification of a Курпатов line matches the catalogued pattern (Air/Form/Substance with the right dimension)." Sub-Outcome of *Voice preservation* / *Reading speed* (whichever the case targets).

**Score components.** PENDING (no mechanical reward function).

**Aggregate / Score range / PASS threshold / Italian-strike band.**
PENDING (no mechanical reward function). Components require an LLM-as-judge harness: one component per assertion in the case (bucket match, dimension keyword present, rationale keyword present). Each would be 0/1 once wired. The case stays in the
PENDING verdict until the harness lands.

## WP-14 When the Wiki PM is given a triple-trail filler, then it tags the line with the Reading-speed dimension

### Set expected result

Dimension contains "Reading speed". Bucket = Air.

### Arrange

- **Input data.**

  > и так далее, и так далее, и так далее

- **Agent.** Same as WP-07.

### Act / Assert

- Same shape as WP-07. Verdict: PENDING.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the role's classification of a Курпатов line matches the catalogued pattern (Air/Form/Substance with the right dimension)." Sub-Outcome of *Voice preservation* / *Reading speed* (whichever the case targets).

**Score components.** PENDING (no mechanical reward function).

**Aggregate / Score range / PASS threshold / Italian-strike band.**
PENDING (no mechanical reward function). Components require an LLM-as-judge harness: one component per assertion in the case (bucket match, dimension keyword present, rationale keyword present). Each would be 0/1 once wired. The case stays in the
PENDING verdict until the harness lands.

## Verdict lifecycle

```
PENDING ──(case authored, runner not yet executed)──▶ PENDING
PENDING ──(runner executes, real == expected)───────▶ PASS
PENDING ──(runner executes, real ≠ expected)────────▶ FAIL
PASS    ──(persona / activation changed; rerun real ≠ expected)──▶ FAIL
PASS    ──(real artefact contradicts expected; spec was wrong)───▶ STALE
STALE   ──(case re-written with rationale)──────────▶ PENDING
```

A `STALE` event is the expensive signal — the spec was wrong
about what the agent should produce.

## Runner

The runner that automates the executable subset lives at
[`/scripts/test-runners/test-wiki-pm-runner.py`](../../../scripts/test-runners/test-wiki-pm-runner.py).
It implements the Act + Assert steps for cases that don't need
agent-level judgement (today: WP-01 through WP-06 — artefact
inspection over `corpus-observations.md`).

WP-07 through WP-14 require agent judgement on a fresh
classification call; they remain `PENDING` until either an
LLM-as-judge harness exists or the architect runs them by
hand. Each case carries the fixture + expected behaviour so a
future runner picks up without re-derivation.

The runner is *not* a test; it is a derived mechanism.
