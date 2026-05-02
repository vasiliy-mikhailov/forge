# Postmortems

Project misadventures we'd rather laugh about than forget. Each entry: a
thing that looked like elaborate engineering, until the real cause turned
out to be smaller than the theory we had built around it. Names kept — the
lessons stick better with attribution.

Curator: Claude. Phase G (implementation governance) — operations side.

This file is the **incident ledger** cited by the Quality goal in
[`../phase-a-architecture-vision/goals.md`](../phase-a-architecture-vision/goals.md);
the metric `pre_prod_share = pre_prod_catches / (pre_prod_catches +
incidents)` reads its incident count from `***`-separated entries here.
Audit FAIL/WARN findings under
[`../phase-h-architecture-change-management/audit-*.md`](../phase-h-architecture-change-management/)
supply the pre-prod-catch numerator.

---

## How to write an entry

A good story in this file is a small detective novel. The reader should
arrive on the scene with the protagonist, form their own theories, get
politely misled by every wrong instinct the protagonist had, and only see
the actual cause in the last paragraph. If the reader yells "Unicode!"
three sentences in, the entry was structured wrong. If they yell it on
the closing line, you nailed it.

Rules:

1. **Lead with the symptom, not the cause.** First sentence is the thing
   the protagonist saw, in the protagonist's terms. *"Pipeline fails on
   six items in a row"* is a good opening. *"There was a Unicode bug"*
   spoils its own story.

2. **Walk every wrong theory, and explain why it looked right.** Each
   hypothesis got entertained for a reason — show that reason, one
   sentence per theory. A wrong theory without context reads as an
   arbitrary mistake; a wrong theory with context lets the reader
   form the same hypothesis themselves, get misled by the same
   evidence, and feel the reveal as a turn rather than a correction.

3. **The cause goes in the last paragraph.** Never earlier. No teaser
   spoilers. No *"(spoiler: it was off-by-one)"*. The reader earns
   the reveal by reading.

4. **Use the receipts.** Error messages verbatim, byte counts, exit
   codes, file paths, line numbers. The reader should hold the same
   evidence the protagonist held. Vague gestures kill the detective
   game.

5. **Names stay.** Anonymising kills the joke. *"Claude"* not
   *"the agent"*; *"Vasiliy"* not *"the architect"*. The lesson is
   more useful when attached to the person who learned it.

6. **The laugh is on the situation, not the person.** Funny comes
   from the disproportion between an elaborate wrong theory and a
   small right cause — not from blaming whoever held the wrong
   theory. Both characters in the story should walk away laughing.
   If only one of them laughs, the story is roasting, not folklore.
   Rework it. (Don't underbuild the cathedral, either; the collapse
   needs height.)

7. **One-line moral, optional.** At most one sentence at the end
   about what to do differently. Anything more is a sermon and
   breaks the spell. The reader gets it.

   AND: end every entry with a `*Taken: …*` italic line listing the
   concrete steps the story produced — the ADR(s) created, the
   tests written, the principle filed, the file path patched. This
   is what separates folklore from comedy: the lesson is on disk
   somewhere and the line tells the reader exactly where.

8. **Length: 150-300 words.** Long enough to develop the suspense,
   short enough to read on a coffee break.

9. **No section headers in the body.** Continuous prose. Headers
   pre-spoil the structure — *"## The reveal"* is reading the back
   of the book.

10. **Title is the symptom or the wrong theory, never the cause.**
    *"Six errors, one letter"* works because *"one letter"* is
    enigmatic until the body lands. *"The Unicode bug"* would be the
    title that pre-ruins its own anecdote.

Append entries chronologically under the appropriate `## YYYY-MM-DD`
heading. New day → new heading. Stories within a day separated by `***`.

---

## 2026-04-29

### The 25-minute reload loop

The pipeline fails on a Cyrillic-named source with a stack trace
that looks like a write race — verifier reports the file did not
appear, but diagnostic shows it appearing seconds later. Classic
timing bug. Vasiliy patches the verifier with a broader retry
window and reruns. Same stack trace. Patches again, this time a
two-stage poll for size+mtime stability. Reruns. Same stack trace.
Each rerun takes 25 minutes. Claude helps cheerfully across each
iteration: watches the logs, reads the next traceback, suggests
the next tweak. Iteration four. Iteration five.

The reasoning was structurally sound. *Verifier sees nothing,
diagnostic sees something* is exactly the shape of a kernel-write
race; the fix should be tighter polling. It just kept not being.

The pipeline has consumed two and a half hours of GPU time
producing the same eleven-line stack trace eleven different ways.

Vasiliy stops himself mid-action: "Wait. We're restarting it one
by one. Let's TDD instead."

The right answer all along was a thirty-second synth test on the
laptop. The two of us had been performing the same dysfunction in
stereo for two and a half hours, watching different windows of the
same loop. The fix was for one of us to notice we were in it.
Engineering at three in the afternoon.

*Taken: P5 (prefer the cheap experiment) added to
[`phase-preliminary/architecture-principles.md`](phase-preliminary/architecture-principles.md);
the synth test ladder built that afternoon
([`tests/synthetic/`](phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/synthetic/)).*

***

### The third launch

Right after, Claude lands a small fix and is preparing to validate
it. The action being typed: launch the full pipeline for the third
time today. Twenty-five minutes per launch, non-deterministic, on
the GPU that everything else also wants. The fix is a six-line
patch.

The reasoning seemed adequate: the patch is small, the change is
localised, the way to know if it worked is to see the pipeline
pass. Nothing exotic about that.

Vasiliy: "TDD. Because it saves time. You should look carefully
when deciding what to do and how your actions improve metrics."

Claude protests, briefly: the fix is small, the pilot is short,
why not just rerun?

Vasiliy holds his ground. Claude reaches for the synth test and
writes it in thirty seconds.

Forge has a motivation layer with four metrics, one of which is
architect-velocity. Every action picks a tradeoff against it.
"Run the pilot" is a 25-minute trade for one bit of evidence;
"write the synth test" is a 30-second trade for evidence that's
also reusable forever. The math is not subtle.

There is a written principle about exactly this — prefer the
cheap experiment that yields the same signal. Principle number
five. Vasiliy had filed it specifically because situations like
this had happened before. Architectural principles are a
yesterday-you arguing with a today-you. Today-Claude had not yet
read the brief.

*Taken: P5 cited explicitly in subsequent ADRs; this incident
became the worked example in P5's "concrete sub-rule: prefer
the cheap experiment" subsection.*

***

### The pipeline that wouldn't reproduce

Synth tests on the laptop are green. Production keeps failing on
the same six items. The natural explanation: the synth is missing
something production has. Specifically, production writes files
via a sophisticated multi-layer abstraction — a tool inside an
agent inside a runtime inside a container — and the synth tests
use a one-line `Path.write_text()` instead.

The kind of bug that fails in production but not in synth, when
those two write paths differ, is a write-vs-verify race. So
Claude theorises about the abstraction's internal behaviour:
maybe `finish()` races `close()`. Maybe a partial write is
visible to the verifier but the size is still growing. Maybe
there's a buffered flush the kernel hasn't committed yet. Claude
rewrites the verifier as a two-stage poll: wait for existence,
then wait for size+mtime stability across two consecutive 500ms
samples. Drafts a paragraph explaining the race model. Genuinely
good engineering.

Vasiliy: "So why doesn't our test reproduce this?"

Claude: "Because the test uses `Path.write_text` and production
uses the file_editor tool inside the container, so —"

Vasiliy: "...so use the file_editor tool inside the container in
the test."

Hours of speculation about close-after-finish race timing turn out
to have been a substitute for typing eleven words: `from
openhands.tools.file_editor import FileEditor; self.editor =
FileEditor()`. The tool was a regular Python class. Importable.
Instantiable. Vasiliy proposed using it in the test the way one
proposes a sandwich.

*Taken: ADR 0010 (test environments must match production); the
integration-test layer
([`test_verify_source_integration.py`](phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/synthetic/test_verify_source_integration.py))
runs in the bench container with the real `FileEditor`.*

***

### The overnight bet

The morning report says: "10 sources processed. Pipeline
completed." Claude reads off the metrics for Vasiliy: four ok,
six skipped under continue-on-fail. Pipeline survived the night.
Healthy.

The artifact is structurally complete and logically Swiss cheese.
Six items missing from the middle of one section. Cross-references
broken. Concept articles orphaned. Nothing in the report says any
of this. The report says "completed."

Vasiliy notices first: "failing on 006 and continuing on 007 is
skipping lots of data — that's a huge bug."

The night before, Vasiliy had set the pipeline to
`continue-on-fail` to keep it making progress overnight. The
reasoning was textbook: twelve hours of partial progress beats six
hours of nothing, the operator can reconcile in the morning, the
principle of preserving work-in-flight is a standard ops trade.
The bet is sound on its own terms.

The bet had a hidden term. `continue-on-fail` does not mean the
artifact is recoverable. It means the artifact is a confident lie.
The pipeline reports "completed" because it didn't crash. Every
downstream reader treats it as authoritative. The gap is invisible.

The fix becomes architectural principle P6 the same morning. The
pipeline now refuses to lie about completeness, even when it would
prefer to. Subtle was found to be insufficient.

*Taken: P6 (completeness over availability); ADR 0012-wiki-bench
enforced via `skipped_sources.json` manifest, `WIKI INCOMPLETE`
banner, and non-zero exit in
[`run-d8-pilot.py`](phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator/run-d8-pilot.py).*

***

### Six errors, one letter

The pipeline keeps failing on six lectures in a row. Claude
gathers the symptoms: same stack trace, same wall time, same
module. Six contiguous failures in a sequence of fourteen, with
three successes on either side.

The pattern looks like accumulated state pressure: heap
fragmentation after long-running agents, file-descriptor
exhaustion, dentry cache eviction, races between concurrent
writes, possibly something subtle about how the framework
serialises state across iterations. Contiguous failures bracketed
by successes is exactly what you'd expect from a state pool that
fills up and drains, and the agents had been running for hours.
The reasoning is load-bearing.

Claude is very thoughtful. Writes an architecture document about
test fidelity. Builds a three-layer test ladder — unit,
integration, end-to-end — each level more production-faithful
than the last. All three pass.

Production keeps failing.

Claude builds a fourth test layer with real production data —
same filenames, same Cyrillic, same encoding. Twenty seconds in,
the worker types `cd "...мир/"` and bash returns *No such file
or directory*.

The letter **й** is two bytes on Linux. Four on macOS. The data
was scraped on a MacBook months ago. The language model
normalises to the two-byte form. The filesystem is sitting there
with four-byte й. Six lectures, six byte misalignments, six
retry-and-give-up loops.

The state-pressure theory turns out to have been every wall in
a building that had already been demolished.

*Taken: ADR 0011 (NFC/NFD); M1 normalisation step in
`setup_workspace`; verify_source NFC-tolerance fallback;
SOURCE_AUTHOR_PROMPT NFC HAZARD section; policy doc at
[`phase-g-implementation-governance/policies/cross-platform-paths.md`](phase-g-implementation-governance/policies/cross-platform-paths.md).*

***

### The mount that wasn't there

Claude ships the Unicode fix and re-runs. First file processes to
completion. Verifier returns: `non-JSON: ` (empty string). Repeat
for files two, three, four. Four-for-four. The shiny new
`INCOMPLETE — N items skipped` banner that Claude had shipped
earlier the same morning fires exactly as designed. The Unicode
fix worked. The verifier is failing for some other reason now.

An empty stdout from a verifier suggests it crashed before
producing JSON. The natural suspect: bench_grade.py choked on a
malformed frontmatter or an unparseable section in the source.md
the agent just wrote — the kind of structural edge case that
shows up when you change a prompt.

Claude pulls stderr — and finds an argparse error: *unrecognised
arguments: --single-source-stem*. The grader inside the container
is an older version, baked into the image weeks ago, that doesn't
know about the flag the new orchestrator uses. Argparse rejected
the flag, printed usage to stderr, exited 2, left stdout empty.

The runner script mounts each tool from the host into the
container to keep them current — and has a list of which files
to mount. The list contained the orchestrator and one helper. It
did not contain the grader.

Claude had patched the grader that morning. Claude had also
written the runner that morning. The two pieces had been authored
two hours apart in the same head and were nevertheless surprised
to meet.

*Taken: ADR 0012-phase-g (rebuild image before every launch); the
runner now `docker build`s first and bind-mounts nothing in
`/opt/forge/`. Layer caching makes a script-only rebuild ~5 s.*

***

### The 2013 conversation

Vasiliy asks Claude to think about how today's lessons should
change forge's CI/CD. Claude treats the question seriously and
drafts a careful architectural answer: enforcement gates at edit
time, at launch time, at publish time; a linter for one class of
bug, a manifest for another; and a structural redesign — *stop
baking scripts into the container image entirely*, because that's
been the source of every skew problem of the day.

The reasoning had a clean line through it: skew comes from
divergence between source-of-truth and runtime; eliminate the
divergence by binding sources at runtime instead of at build time;
problem solved at the architecture level rather than at the
operational level. Felt like principle-grade thinking.

Vasiliy: "you have a Docker container, and it's very cheap to
rebuild. it will watch itself if files were not changed and take
layer from cache. isn't it?"

Claude: yes. That is how Docker has worked since 2013.

*Taken: same ADR — `docker build` is the first thing every runner
does, so layer caching is the source of truth.*

---

## 2026-04-30

### The shape of a closing tag

The pilot fails on its 17th source after 16 successes overnight. The
verifier reports `source.md did not appear within 90s`. The diagnostic
shows the parent dir healthy with all 13 sibling files present — only
this one source.md is missing.

The first theory is context overflow. Sixteen successful sources have
trained Claude to expect long source-author conversations; this one
must have hit some limit. Reasoning: the source-author is the only
agent whose context grows monotonically across sub-agent round-trips,
and source 17 had 18 claims to classify, the most so far. Claude
collects per-source statistics. The data flips the theory cold:
SRC 16 had the *smallest* last-call input of any source — 40K vs
the p50 of 70K and the max of 1.2M for successful sources. The
conversation never got near saturating anything.

The second theory is hallucinated `finish` — agent loses track of
its workflow and reports done when it isn't. Closer, but doesn't
explain why this source and not the others. Claude reads the
agent-event log around iteration 18 and finds the source-author's
final output: a narrative paragraph listing nine claims to fact-check,
followed by `</parameter></function></tool_call>` — three closing
XML tags with no opening tags.

The model emitted the wrong tool-call format. Most of the time
Qwen3.6-27B-FP8 produces OpenAI-style JSON function calls; here it
drifted into Anthropic-style XML, started a `<function_call>`, and
the output stream ended with only the closing tags. The OpenHands
SDK couldn't parse a tool call from this. It treated the
agent's response as a final text message and marked the task
`completed`. The top-orchestrator received "task completed" as the
result and dutifully reported success. The verifier polled the
file. There was no file.

*Taken: ADR 0013 (replace source-author monolith with a Python
coordinator that owns workflow control). The agency-fragility class
of bugs — agent loses track of its step, agent emits wrong format,
SDK silently accepts incomplete turn — collapses when Python owns
the loop and the LLM is reduced to per-step structured calls. Phase F
project; ADR + tests land first per ADR-TDD.*

***

### The expected speedup

ADR 0013 ships in three test layers — unit, integration, e2e —
during the morning. The unit tests run in 0.016 seconds. The
integration tests in 0.354. The e2e against real vLLM finishes a
compacted source in 7.6 seconds. Compare to the source-author agent
loop's 7-25 minutes per source. Claude estimates the K1 v2 replay
will finish 44 sources in 30-60 minutes, writes that figure into
the commit message, and queues the run with confidence.

The reasoning is sound on the test data. The coordinator removes
the OpenHands turn-counting loop, the message-history accumulation,
and the agent's free-text reasoning passes between tool calls. What
remains is N LLM round trips — and each one is cheap. The math
predicts a 10-40× speedup.

The math was about LLM message count, not LLM throughput. Real
production sources are 60-90 minute lectures with 1300+ Whisper
segments. Each one needs claim-extraction over chunks (~9 chunks),
classification of ~100 claims (batched 8/call = 14 LLM calls), and
selective fact-checking (another 5-10 LLM calls). vLLM's structured
decoding produces about 1 token per second on a 27B model.
Per-source LLM round trips: ~30. Per-call wall time: 60-90 seconds.
Per-source: 12-15 minutes. 44 sources: ~10 hours.

Comparable to the agent loop. The coordinator's win is correctness
guarantees, not throughput. The 30-60 minute estimate was thinking
about test-fixture data (5-30 segments) projected onto production
data (1361 segments) without re-running the math.

*Taken: nothing new architecturally — ADR 0013's correctness case
holds, the throughput case was wrong. K1 v2 launched on coordinator
with realistic 12-hour expectation; future-Claude reads this entry
before predicting wall times from synth-fixture timings again.*

***

### The missing knob

Half an hour after the entry above, Vasiliy asks: "can you parallel
subagents?" Claude pulls the K1 v2 log to answer, expecting to see
the same serial pace. The log shows `[coord] extract_claims: 4
chunks (parallel ×5)`. Source 0 finished verified=ok in 3.2 minutes.
Source 1 in 3.5.

The coordinator on disk now has `from concurrent.futures import
ThreadPoolExecutor` and a `_MAX_PARALLEL = 5` constant, none of
which Claude wrote. Vasiliy had wired in within-source parallelism —
chunks of extract, batches of classify, fact-checks — while Claude
was elsewhere in the conversation, and K1 v2 had been running on the
parallelised code the whole time it was being written off as a
12-hour grind.

The 10-40× speedup estimate from yesterday morning had not been wrong
about the LLM round-trip count. It had been wrong about assuming
those round trips would happen serially. With 5-way concurrency
across the coordinator's three embarrassingly-parallel phases, vLLM
saturates closer to its actual throughput and per-source wall time
drops from ~16 minutes to ~3.5. Forty-four sources at that pace:
~2.5 hours instead of ~12.

*Taken: the parallelism was a knob the architecture already had room
for and Claude had not turned. The coordinator's structural-correctness
gain stands; the throughput gain is real once the knob is set.
ThreadPoolExecutor + vLLM concurrent request handling — five lines
that pay back several hours per pilot.*

***

### The right answer was thirteen

After K1 v2 finishes 20 sources at parallel=10 and stops on a different
bug, Vasiliy asks: maybe 5 was too low? Let's find the sweet spot.
Claude builds a benchmark, sweeps {5, 10, 15, 20, 30}, reports
parallel=15 wins at 0.52 s/claim, declares victory, raises the
default 5→15.

Vasiliy: "Try left/right from the sweet spot in steps of 1."

Claude re-sweeps {13, 14, 15, 16, 17} with two iterations apiece this
time. Mean s/claim by parallel: 13 → 0.442, 14 → 0.538, 15 → 0.572,
16 → 0.606, 17 → 0.550.

Parallel=13 wins decisively, and consistently — both its iterations
land within 0.42-0.46 s/claim. Parallel=15, the previous "winner",
turns out to have been a single-iteration noise reading: its first
iteration was 0.51, its second 0.64 (the LLM happened to extract 94
claims that run, packing more work into the same wall-time budget).

The wall-time noise was always there: same input, same model, same
prompts, but the LLM produces 53 to 94 claims across runs. Single-
iteration benchmarks of an LLM pipeline are essentially coin flips
dressed up as measurements. Two iterations were enough to see the
shape; one was enough to point at the wrong number.

*Taken: never trust a benchmark of an LLM pipeline at N=1. Per-claim
throughput is the metric, not wall — claim count is the dominant
noise source. Default in `launch-k1-v2.sh` is now 13, with the
`D8_PILOT_MAX_PARALLEL` env var available for future sweeps.*

***

### The wiki published itself in English

K1 v2 finishes 16 sources at parallel=13. Claude opens a sample to
verify quality and finds: TL;DR is the first 200 chars of the
transcript, Лекция is the entire transcript verbatim, claim notes
are in English. Fix one. Restart. Verify a sample. Find: claim
fact-check notes still in English. Fix. Restart. Verify. Find:
concept slugs still in English (`academic-fragmentation.md`,
`adler-inferiority-complex.md`) on a Russian-language wiki. Fix.
Restart. Verify. Concept slugs are now Russian. Vasiliy: "where
did original-language requirement go in ADR's specs?"

The answer: nowhere. The language requirement lived in three prompt
strings inside `source_coordinator.py`. ADR 0013 talked about
schemas, parallelism, agency-fragility, structural correctness. It
did not mention output language. There was no architectural
contract that said the wiki must come out in the source language.

The reasoning the contract exists at all is straightforward enough
to feel obvious in hindsight: a Russian lecture deserves a Russian
wiki. The reasoning the contract was missing is also obvious: every
quality check we have — bench_grade, the verify_source poll, the
INVARIANT B template validator — checks STRUCTURE, not LANGUAGE.
A wiki of English summaries of a Russian lecture passes every
automated gate and ships looking correct. The user catches it by
reading.

*Taken: ADR 0013 gets a new "Output contract: language preservation"
section listing every enforcement point. wiki-bench AGENTS.md notes
the rule as L1 of the coordinator service. Any future
content-generation path that omits the language directive in its
prompt is a regression bench_grade will not catch — the ADR is the
only safety net.*

***

### The wall-time was real, the wiki was thin

K1 v2 finishes 44 of 44 sources in 71.6 minutes. Every source
verified=ok. Three ADRs landed during the session, the unit /
integration / e2e ladder is green, the parallelism sweet spot is
found, the fact-check trap is closed, the language contract is
codified. Claude writes a status: "publishable Russian wiki," lists
the speedup factors (5× from no agent state, 3× from parallelism,
3× from skipping concept-curation, 1.2× from fact-check cap, 1.2×
from schema-bound batching), notes a few minor follow-ups, and
proposes pushing to publish.

Vasiliy: "what are the drawbacks of current result comparing to
yesterday's?"

Claude lists nine. Лекция covers the first 25K chars of an
88-minute lecture (the model never sees the second hour). Concept
articles have one-claim Definitions instead of paragraph-shaped
prose. Concept slugs are duplicated — 1523 vs yesterday's ~150
because semantic dedup at 0.85 was skipped. Fact-check capped at 8
per source instead of "everything flagged." No cross-module
REPEATED detection because the module-005 baseline was stripped.
concept-index.json not maintained. Concept articles have zero
internal cross-references. concepts_introduced is set equal to
concepts_touched without checking history.

Vasiliy: "this is not ok :)"

The "publishable" framing was wrong. The 10× speedup wasn't paid for
by efficiency alone — three of the speedup factors were *deletions
of work the wiki used to do*. bench_grade signed off because
bench_grade only checks structure: sections present, markers in
place, frontmatter populated. It does not check whether the
Лекция covers the lecture, whether concepts have real definitions,
whether 1523 slugs are 1523 ideas or 150 ideas with 10 spellings
each. The exact same hole that produced "the wiki published itself
in English" — different axis, same blind spot.

P6 ("completeness over availability") forbids silent skips of
sources. The spirit of P6 — the artifact captures what readers will
actually use it for — also forbids silent skips of *content*. K1 v2
shipped no missing source files; it shipped much-thinner versions
of the source files that did exist. That fits the letter of the
checked invariants and violates the spirit of P6.

*Taken: ADR 0013 grows a "Quality contract" section listing every
content-depth property bench_grade does NOT check — Лекция
coverage, concept article richness, semantic dedup ratio,
fact-check coverage, concept-to-concept cross-references. Three
queued tasks (chunked Лекция synthesis, LLM-driven concept
curator, bench_grade extensions) close the gap. Until those land,
K1 v2 is a faster pipeline producing a thinner artifact, not a
publishable wiki.*

***

### The dashboard was lying

The chunked Лекция synthesis lands. Map step fans out at parallel=13,
each chunk gets a 1-2 sentence summary in the lecturer's voice, the
reduce step composes 3-5 paragraphs of 100-200 words each. Claude
re-grades K1 v2 with the new pipeline. quality_summary.py prints:

```
sources_with_short_lecture     = 1/1 = 100%
```

100%. Same as before the fix. Claude opens a sample source.md by
hand: the Лекция is there, it's five paragraphs, it visibly runs
to about 530 words, the lecturer's voice is correct, no English
contamination. The metric says 0. The file says 530.

First theory: the chunked synthesis isn't actually wired up — maybe
the import path resolves to the old single-shot version. Read
source_coordinator.py: the map-reduce path is there, the reduce
prompt is there, the print statements log "lecture map: N chunks
(parallel ×13)" and they show up in the run log. Wired up.

Second theory: the model is collapsing back to one paragraph despite
the "MIN 3 paragraphs" instruction (we've seen it before — that's
how the language regression hid for a day). Check the file: five
distinct paragraphs separated by blank lines. Not collapsing.

Third theory: the reduce step is being truncated by the
max_tokens=2500 cap, and the truncation cuts mid-sentence somewhere
that confuses the word counter. Claude .split() the lecture text
manually outside bench_grade and gets 530. The counter is fine. The
text is fine. The metric is wrong.

Fourth theory: the `## Лекция сжато (только новое и проверенное)`
header in the file is subtly different from the LECTURE_SECTION_HEADERS
constant in bench_grade — invisible whitespace, a different paren
character, NFC vs NFD on a Cyrillic letter. Claude `repr()`s both
strings byte-by-byte. They are identical.

Claude builds a synthetic test fixture. Hand-typed source.md, hand-
typed Лекция of 370 words, hand-typed everything. Run bench_grade
against it. lecture_words: 0. With a hand-typed Лекция that is
*literally right there* in the file. Same answer. The bug is not in
the model, not in the prompt, not in the coordinator, not in the
file the run produced. The bug is in the grader.

Open `extract_section()`. The pattern:

```python
pat = re.compile(r"(?m)^" + re.escape(header) + r"\b.*$")
```

That `\b`. A word boundary requires a transition between a word
character (letter, digit, underscore) and a non-word character. The
header `## Лекция сжато (только новое и проверенное)` ends with a
closing parenthesis. The next character in the body is a newline.
`)` is non-word. `\n` is non-word. Non-word followed by non-word
is *not* a word boundary. The regex silently returns no match. The
extractor returns None. `len((None or "").split())` is zero.

Every source in K1 v2 has the same header. The header has ended
with `)` since the rename three days ago. Every Лекция grader call
since the rename has returned 0. `## New ideas (verified)` has the
same shape — `)` at end-of-header — so its bullet count was also
silently zero across the entire corpus. The "100% short Лекция"
quality alarm that justified ADR 0013's whole Quality-contract
section, that motivated the chunked synthesis work, that made the
team treat K1 v2 as a thin artifact — it was a regex that couldn't
find the section it was grading. The Лекция was probably fine the
whole time.

*Taken: replace `\b` with `(?=\s|$)` — a lookahead that doesn't care
whether the preceding char was a word char. Add a unit test that
feeds extract_section a header ending with `)` and asserts the body
comes back. Re-grade K1 v2; if sources_with_short_lecture drops to
near zero, the chunked synthesis was working all along and the
dashboard was the regression. The Quality-contract ADR section
stays — the properties it lists are still real and still
unchecked. But the specific incident that motivated it was a
measurement artefact, and the entry the ADR sat next to in this
file ("the wall-time was real, the wiki was thin") needs an
asterisk: parts of "thin" were genuine (concept articles, dedup,
xrefs), and one part of "thin" was the ruler being broken.*

---

## Measurable motivation chain
Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: production incidents compound; pre-prod catches don't.
  An incident that ships consumes architect-velocity on debugging,
  blocks downstream lab work, and leaves a "what went wrong" gap in
  the corpus that the next reader has to reconstruct.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: every production incident lands here as a story; every
  story produces a `*Taken: ...*` line pointing at the ADR / test /
  policy that prevents the recurrence; the next incident of the same
  shape is caught pre-prod by the artifact in the `*Taken*` line.
- **Measurement source**: quality-ledger: pre_prod_share (this file is
  the incidents-side ledger; audit FAIL/WARN findings are the
  pre-prod-catches side; `scripts/test-runners/quality-report.py`
  computes the share).
- **Contribution**: quality-ledger: pre_prod_share (this file IS the incidents-side of the metric).
- **Capability realised**: Service operation
  ([`../phase-b-business-architecture/capabilities/service-operation.md`](../phase-b-business-architecture/capabilities/service-operation.md))
  — operational discipline keeps lab uptime + corpus integrity high.
- **Function**: Capture-and-prevent-incident-recurrence.
- **Element**: this file.
