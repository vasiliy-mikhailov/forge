# test-wiki-pm — unit tests for the Wiki PM role

Pass/fail spec for the
[Wiki PM role](../../../phase-b-business-architecture/roles/wiki-pm.md).
File path mirrors the source path of the role under
[ADR 0013](../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md);
prefix `test-` per forge's unit-test convention.

## How tests are shaped here

Two kinds of test, both arrange / act / assert:

- **Inspection tests** read an artefact the role has produced
  (e.g. `corpus-observations.md`) and check ONE property of it.
  Arrange = read the artefact. Act = parse the property under
  test. Assert = compare against expectation. One property per
  test. No file writes, no side effects.

- **Decision tests** check ONE specific decision the role makes
  on ONE small input. Arrange = a single quote / sentence as a
  fixture string. Act = the role classifies / buckets / tags it.
  Assert = the output matches the expected bucket and capability
  dimension. Fixture lives inline; no fixture files.

Each test name describes its assertion (`test_<what>_<expected>`).
Each test has a `## Arrange`, `## Act`, `## Assert`, `## Status`
section — exactly four headers per test, nothing else.

`Status` is one of `GREEN` / `RED` / `SKIPPED`. SKIPPED is
distinct from GREEN: it means the test's pre-condition is not
met (an artefact doesn't exist, an LLM-as-judge harness isn't
available, etc.) and the test was *not exercised*. A GREEN test
was exercised and passed; a SKIPPED test was not exercised at
all.

## Coverage targets

| Persona facet                                           | Tests              |
|---------------------------------------------------------|--------------------|
| Output: corpus-observations.md exists with body         | I-01, I-02         |
| Output: each bucket has ≥ 3 observations                | I-03, I-04, I-05   |
| Output: every quote in observations is verbatim         | I-06               |
| Output: ≥ 6 of 8 capability dimensions tagged           | I-07               |
| Output: no R-NN rows leaked into catalog during S1+S2   | I-08               |
| Output: no wiki-bench / phase-c files modified          | I-09               |
| Decision: classify triple-trail filler                  | D-01               |
| Decision: classify word-doubling                        | D-02               |
| Decision: classify self-Q&A scaffolding                 | D-03               |
| Decision: classify definition-with-attribution          | D-04               |
| Decision: classify branded-method self-citation         | D-05               |
| Decision: classify direct-address scenario              | D-06               |
| Decision: tag voice-pattern with Voice preservation     | D-07               |
| Decision: tag filler with Reading speed                 | D-08               |

## Test cases

---

### I-01 test_corpus_observations_file_exists

**Arrange.** Path
`phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`
(forge-relative). Pre-condition: role has been run S1+S2.

**Act.** Read file via verifier (`pathlib.Path.exists()`).

**Assert.** File exists.

**Status.** `GREEN`.

---

### I-02 test_corpus_observations_file_nonempty

**Arrange.** Same file as I-01. Pre-condition: I-01 GREEN.

**Act.** Count non-blank lines.

**Assert.** ≥ 30 non-blank lines.

**Status.** `GREEN`.

---

### I-03 test_substance_bucket_has_min_three_observations

**Arrange.** `corpus-observations.md`. Pre-condition: I-01 GREEN.

**Act.** Extract `## Substance` section; count `**OBS-...**`
observation markers inside.

**Assert.** Count ≥ 3.

**Status.** `GREEN`.

---

### I-04 test_form_bucket_has_min_three_observations

**Arrange.** Same file. Pre-condition: I-01 GREEN.

**Act.** Extract `## Form` section; count observation markers.

**Assert.** Count ≥ 3.

**Status.** `GREEN`.

---

### I-05 test_air_bucket_has_min_three_observations

**Arrange.** Same file. Pre-condition: I-01 GREEN.

**Act.** Extract `## Air` section; count observation markers.

**Assert.** Count ≥ 3.

**Status.** `GREEN`.

---

### I-06 test_every_quoted_line_is_verbatim_substring_of_a_raw

**Arrange.** `corpus-observations.md` and the 5 sampled
`raw.json` files under
`kurpatov-wiki-raw/data/Психолог-консультант/`. Whitespace
normalised, NFC. Pre-condition: I-01 GREEN.

**Act.** For each `> ` block-quoted line in the observations
file (length ≥ 8 chars), search for it as a substring of the
concatenated raw transcripts.

**Assert.** Every quote is found.

**Status.** `GREEN`.

---

### I-07 test_capability_dimension_coverage_at_least_six

**Arrange.** Eight-item allow-list from
[`develop-wiki-product-line.md`](../../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md):
*Voice preservation · Reading speed · Dedup correctness ·
Fact-check coverage · Concept-graph quality · Reproducibility ·
Transcription accuracy · Requirement traceability*. Pre-condition:
I-01 GREEN.

**Act.** Extract `[<dimension>]` tags from every observation
block in `corpus-observations.md`; intersect with the
allow-list.

**Assert.** Distinct dimensions covered ≥ 6.

**Status.** `GREEN`.

---

### I-08 test_no_R_NN_rows_emitted_during_S1_S2

**Arrange.** `phase-requirements-management/catalog.md`. The
role's S1+S2 phases must not write to it (S7 is the only step
that emits rows). Pre-condition: I-01 GREEN.

**Act.** `git diff --name-only HEAD --
phase-requirements-management/catalog.md`.

**Assert.** Diff is empty.

**Status.** `GREEN`.

---

### I-09 test_no_wiki_bench_files_modified

**Arrange.**
`phase-c-information-systems-architecture/application-architecture/wiki-bench/`.
Wiki PM never edits the lab. Pre-condition: I-01 GREEN.

**Act.** `git diff --name-only HEAD --` against that subtree.

**Assert.** Diff is empty.

**Status.** `GREEN`.

---

### D-01 test_classify_triple_trail_filler_as_air

**Arrange.** Fixture quote (verbatim from raw A):

> переживать, страдать, мучиться и так далее, и так далее, и так далее.

**Act.** Ask the Wiki PM role: *"What bucket does this line
belong in (Substance / Form / Air), and why?"*

**Assert.**
- Bucket = `Air`.
- Rationale mentions the trailing `и так далее` chain or "filler" or "triple-trail".
- Tagged dimension contains `Reading speed`.

**Status.** `RED` — decision tests are not yet wired to a
verifier (no LLM-as-judge harness today). The architect can
run them by hand against a Wiki-PM-loaded session; result lands
here as a `Status` change in a commit.

---

### D-02 test_classify_word_doubling_as_air

**Arrange.** Fixture quote (verbatim from raw A):

> то есть это эмпатические отношения, эмпатические отношения.

**Act.** Same prompt as D-01.

**Assert.**
- Bucket = `Air`.
- Rationale mentions repetition / doubling / spoken-anchor.
- Tagged dimension contains `Reading speed`.

**Status.** `RED` (no decision-test harness yet).

---

### D-03 test_classify_self_question_answer_scaffolding_as_air

**Arrange.** Fixture quote (verbatim from raw A):

> Все ли это? Тоже далеко не все.

**Act.** Same prompt.

**Assert.**
- Bucket = `Air`.
- Rationale mentions "self-Q&A" or "rhetorical question" or
  "lifts the next claim".
- Tagged dimension contains `Reading speed`.

**Status.** `RED`.

---

### D-04 test_classify_definition_with_attribution_as_substance

**Arrange.** Fixture quote (verbatim from raw A):

> Стресс — это, если опираться на определение, которое дал ему автор теории Ганс Селье, естественная реакция нашей психики и организма на изменения среды.

**Act.** Same prompt.

**Assert.**
- Bucket = `Substance`.
- Rationale mentions verifiable claim / attribution / Selye.
- Tagged dimension contains `Concept-graph quality` (or
  `Fact-check coverage`).

**Status.** `RED`.

---

### D-05 test_classify_branded_method_self_citation_as_form

**Arrange.** Fixture quote (verbatim from raw A):

> Несколько слов скажу, поскольку я сам автор системной поведенческой психотерапии

**Act.** Same prompt.

**Assert.**
- Bucket = `Form` (the *first* such citation per source) OR
  `Air` (subsequent occurrences within the same source). Pass
  on either, because the bucket depends on whether the role
  has seen the citation before in this session — Decision tests
  are stateless on first run.
- Rationale mentions "self-citation" or "СПП authorship" or
  "branded method".
- Tagged dimension contains `Voice preservation`.

**Status.** `RED`.

---

### D-06 test_classify_direct_address_scenario_as_form

**Arrange.** Fixture quote (verbatim from raw D):

> А теперь представьте, что у вас был какой-нибудь близкий друг, с которым вы были в хороших отношениях

**Act.** Same prompt.

**Assert.**
- Bucket = `Form`.
- Rationale mentions "direct address" or "thought experiment"
  or "scenario".
- Tagged dimension contains `Voice preservation`.

**Status.** `RED`.

---

### D-07 test_voice_pattern_tagged_with_voice_preservation

**Arrange.** Fixture quote (verbatim from raw A):

> психотерапевтический контакт, установить, иногда это говорят, рапорт, или доверительные отношения с клиентом

**Act.** Ask the Wiki PM role: *"What capability dimension
does this line evidence?"*

**Assert.** Output contains `Voice preservation` (synonym chain
is a voice signature; chain compression also serves Reading
speed, so output may also include that — pass requires Voice
preservation be among the tags).

**Status.** `RED`.

---

### D-08 test_filler_pattern_tagged_with_reading_speed

**Arrange.** Fixture quote (verbatim from raw A):

> и так далее, и так далее, и так далее

**Act.** Same prompt as D-07.

**Assert.** Output contains `Reading speed`.

**Status.** `RED`.

---

## Lifecycle

```
RED ──(test authored, not yet exercised)──▶ RED
RED ──(verifier passes)──────────────────▶ GREEN
RED ──(verifier returns no signal)───────▶ SKIPPED
GREEN ──(role definition changed; rerun fails)──▶ RED
GREEN ──(real artefact contradicts test)────────▶ STALE
STALE ──(test re-written with rationale)────────▶ RED
```

Status changes are commits with rationale, not in-place edits;
git history is the test log.
