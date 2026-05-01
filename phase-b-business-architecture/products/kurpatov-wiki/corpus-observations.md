# Kurpatov-wiki — corpus observations

S1 + S2 output of the Wiki PM role per
[`/phase-requirements-management/wiki-requirements-collection.md`](../../../phase-requirements-management/wiki-requirements-collection.md).
Walked 2026-04-30 against `kurpatov-wiki-raw` modules
*Психолог-консультант / 000 Путеводитель / 001 Глубинная / 005 Природа конфликтов*.
Subsequent steps (S3–S7) cite observations from this file by ID
(`OBS-<raw>-NNN`).

The capability dimensions referenced in observation tags come
from
[`/phase-b-business-architecture/capabilities/develop-wiki-product-line.md`](../../capabilities/develop-wiki-product-line.md):
**Voice preservation**, **Reading speed**, **Dedup correctness**,
**Fact-check coverage**, **Concept-graph quality**,
**Reproducibility**, **Transcription accuracy**,
**Requirement traceability**.

## Corpus sample (S1)

| ID | raw.json path (under `kurpatov-wiki-raw/data/Психолог-консультант/`) | words | format | structural notes |
|----|--------------------------------------------------------------------|-------|--------|-------------------|
| A  | `000 Путеводитель по программе/000 Знакомство с программой «Психолог-консультант»/raw.json` | 9 963 | spoken, 88-min lecture | dense free speech; full live-delivery features (filler, repairs, asides); single ~10K-word block, no segment-level paragraph breaks |
| B  | `000 Путеводитель по программе/002 Вводная лекция в программу/raw.json` | 3 391 | written конспект (PDF→text) | already-edited synopsis of A; section headers in CAPS; running-header artefact `ГЛУБИННАЯ ПСИХОЛОГИЯ И ПСИХОДИАГНОСТИКА В КОНСУЛЬТИРОВАНИИ` repeats 12× as page-breaks; A→B compression ratio = 0.34 (calibration band for the condense capability) |
| C  | `005 Природа внутренних конфликтов.../000 Вводная лекция. Базовые биологические потребности.../raw.json` | 8 532 | spoken, module 005 intro | denser conceptual content (потребности, инстинкты), higher concept-density; same Курпатов voice as A |
| D  | `005 Природа внутренних конфликтов.../001 №1. Базовая социальная потребность.../raw.json` | 8 374 | spoken, module 005 #1 | first lecture *of* a module (not intro *to* a module); more claims per minute than C |
| E  | `001 Глубинная психология и психодиагностика.../000 № 1. Вводная лекция о дисциплине/raw.json` | 5 264 | spoken, glubinnaya intro | medium length; bridges module 000 (programme intro) and module 001 (subject matter) |

The major formats this wiki must handle:

1. **Spoken free-form lecture** (A, C, D, E) — Whisper-segment
   raw, conversational tempo, full Курпатов voice features.
2. **Written конспект** (B) — already partly de-aired; serves
   as the human-edited reference for compression-ratio
   calibration.

## S2 — Inventory observations

Each observation: `**OBS-<raw>-NNN [Dimension(s)]** (location)`,
verbatim quote in block-form, then a short note on what the
observation evidences. Quotes are exact substrings of the raw
transcript text after whitespace normalisation; verifier confirms
this mechanically (T-WP-01 acceptance #3, #4).

## Substance

Actual content the source conveys — what wiki readers come for.
Should survive into the final output.

**OBS-A-001 [Concept-graph quality]** *(raw A, ≈25% mark)*

> Стресс — это, если опираться на определение, которое дал ему автор теории Ганс Селье, естественная реакция нашей психики и организма на изменения среды.

A definition with attribution to a primary source (Selye). This
is the kind of claim that *must* survive both the condense step
and the fact-check step intact — the Selye attribution is
verifiable.

**OBS-A-002 [Concept-graph quality][Voice preservation]** *(raw A, chunk 4)*

> оперцепция – это субъективное наслоение на этот наш перцептивный комплекс.

Original conceptual definition — Курпатов's coinage of "оперцепция"
as a layer over perception. Substantive content that doubles as
voice signature (the term is his); both the proposition and the
neologism must reach the wiki.

**OBS-A-003 [Concept-graph quality]** *(raw A, chunk 4)*

> базовые потребности, потребность в самозащите, в выживании, потребность в социальном взаимодействии и определенных социальных результатах, и потребность сексуальная

Three-base-needs taxonomy. Enumeration of distinct concepts —
each becomes a candidate concept-article slug. The taxonomy is
referenced in B's "Базовые биологические потребности" curriculum
listing, confirming it's a load-bearing organising scheme.

**OBS-B-004 [Concept-graph quality]** *(raw B, line 1 ≈ first sentence)*

> Технология факт-карт основана на самых передовых исследованиях работы мозга

Branded-method introduction (факт-карты). A real technique, a
real concept slug, but the framing fuses substance with marketing
("самых передовых") — the substance survives, the qualifier
should drop.

**OBS-C-005 [Concept-graph quality]** *(raw C)*

> лимбическая система, она производит эти наши с вами базовые потребности

Cross-module concept link: C connects лимбическая система
(neuro) to базовые потребности (psychology). Concept-graph
quality demands the link survives — both concepts already
appear in module 000 raws; this is a `REPEATED` claim in
authoring terms.
**OBS-B-018 [Concept-graph quality]** *(raw B, "формула невроза" section)*

> Согласно нашей генетической программе, мы должны жить в живой природе, а не в мегаполисах, в небольших группах близких нам людей

The evolutionary-mismatch claim — psychology-vs-civilization
foundation of Курпатов's neurosis theory. Substantive
testable proposition; survives as a concept the wiki should
catalogue.

**OBS-B-019 [Concept-graph quality]** *(raw B, "формула невроза" section)*

> конфликт биологии и культуры внутри нашей психики

Coined load-bearing term — the fundamental conflict
Курпатов's whole theory orbits. Concept-graph candidate slug;
must survive condense.

**OBS-A-020 [Concept-graph quality]** *(raw A, chunk 4, neuroscience excursion)*

> лимбическая система устроена ядрами, там агрегации нервных клеток

Substantive neuroscience claim with verifiable structure (the
лимбическая система IS organised as ядра / nuclei, fact-
checkable against neuroscience textbooks). Pairs with
fact-check coverage as a candidate for primary-source
citation.

**OBS-B-021 [Concept-graph quality]** *(raw B, СПП section)*

> на знаниях о работе его базовых нейронных сетей, отвечающих за взаимодействие сознательных убеждений и подсознательных установок

The neuroscience-foundation claim of СПП (Системная
поведенческая психотерапия). Substantive scientific framing;
testable against neuroscience literature on default-mode /
salience networks.

**OBS-B-022 [Concept-graph quality]** *(raw B, "формула невроза" section)*

> дистресс приводит к сбоям

The compressed central claim of Курпатов's neurosis model.
Six words; high information density; survives any condense
pass.


## Form

Recurring patterns of voice, structure, transitions.
Distinguishes Курпатов from a generic encyclopedic register —
a wiki that strips form collapses into "any psychology
encyclopedia."

**OBS-A-006 [Voice preservation]** *(raw A, chunk 1, ≈40% mark)*

> Если мы вспомним Эпиктета, который говорил, что вещи не бывают хорошими или такими, или плохими, такими их делают наши отношения к ним, то это он рассказывал именно про оперцептивное поведение.

Authority retrofitted into Курпатов's taxonomy. The Эпиктет
paraphrase carries actual content (the perceptive-relativity
claim) but the framing — "this is what *I* mean by оперцептивное"
— is voice. Loose paraphrase of an external author with
self-attribution of the framework is a Курпатов signature; should
survive condense, but the claim itself enters the fact-check
queue (does Epictetus actually map to оперцептивное?).

**OBS-A-007 [Voice preservation]** *(raw A, chunk 4, ≈40% mark)*

> Несколько слов скажу, поскольку я сам автор системной поведенческой психотерапии, почему в принципе потребовалось вводить это новое понятие.

Branded-method self-citation: "I am the author of СПП." A real
authorship claim (Курпатов did originate СПП) but the
self-citation framing recurs N times across the lecture. The
*first* occurrence carries the attribution; subsequent ones are
redundancy — the wiki should keep one, drop the rest.

**OBS-A-008 [Voice preservation][Concept-graph quality]** *(raw A, chunk 1, ≈30% mark)*

> создать с ним так называемый психотерапевтический контакт, установить, иногда это говорят, рапорт, или доверительные отношения с клиентом, то есть это эмпатические отношения, эмпатические отношения.

Synonym-chain pattern: 4 near-synonyms denoting the same
concept ("психотерапевтический контакт" ≈ "рапорт" ≈
"доверительные отношения" ≈ "эмпатические отношения"). The
*equation* is the substance — concept identification of one
slug under multiple labels. The chain itself is voice; the wiki
should record the equation once and drop the in-prose listing.

**OBS-A-009 [Voice preservation]** *(raw A, chunk 1, ≈55% mark)*

> наши участники наших курсов, они очень ценят возможность регулярно отрабатывать на практике те вопросы, которые у нас есть.

Affective-cohort framing: "наши участники / наших курсов / у
нас есть" — repeated WE-binding. Substance is null (this is
an audience-management aside about engagement); the form is
characteristic. Drop entirely; survives only the curriculum-
listing in S6.

**OBS-D-010 [Voice preservation]** *(raw D, ≈ mid-lecture)*

> А теперь представьте, что у вас был какой-нибудь близкий друг, с которым вы были в хороших отношениях

Direct-address with vivid anchor scenario. A signature Курпатов
move — a thought experiment that lands an abstract claim about
social attachment. Form is distinctive; the scenario often *is*
the content (the mental image survives in the reader where the
abstract claim wouldn't). Must survive condense.
**OBS-B-023 [Voice preservation]** *(raw B, end of stress section)*

> Поверьте, это уже само по себе даёт невероятное чувство облегчения!

Audience-direct emotional appeal ("Поверьте" + exclamation).
Курпатов signature — bridges between abstract claim and
reader emotion. Survives as voice; the claim it lifts
("understanding stress brings relief") survives as substance.

**OBS-A-024 [Voice preservation][Reading speed]** *(raw A, chunk 1, opening)*

> Прежде всего, это Академия Психологии и Мышления, и нам нужно стать с вами психологами.

Lecture-meta opener fused with curriculum framing. "Прежде
всего" is voice-organisational (signposts the talk's
structure); the "АПиМ + стать психологами" content is
program-listing not psychology — a Form/Air boundary case.
Drop the meta opener, keep the APM cross-link as a single
structural reference.

**OBS-B-025 [Voice preservation]** *(raw B, end of глубинная section)*

> Не случайно я люблю называть подход личностно-ориентированной терапии — «гуманистическим континуумом системной поведенческой психотерапии»

Branded-method self-citation by re-naming. "Я люблю называть"
is the signature move — Курпатов claims naming-rights over
how a different school's approach maps into his. Form is
distinctive; the renaming ("гуманистический континуум") is
a candidate concept slug if the wiki adopts it.

**OBS-A-026 [Voice preservation]** *(raw A, chunk 4, near Фрейд)*

> Возможно, вы слышали знаменитое объяснение Фрейда нашей творческой активности

Audience-prior-knowledge framing ("Возможно, вы слышали") +
sublimation example. Voice-signature setup for an example;
the Фрейд-paraphrase that follows is substance, the framing
is form. Drop the framing in condense, keep the example.

**OBS-A-027 [Voice preservation]** *(raw A, chunk 1, mid)*

> Что ж, со знаниями мы разобрались, и, соответственно, у нас возникнут навыки

Discourse-marker section-bridge ("Что ж, … разобрались")
fused with "соответственно у нас возникнут". Pure spoken
delivery; provides paragraph segmentation in the absence of
markup. Form: drop in writing, infer paragraph break.


## Air

Material that, when removed, doesn't change the substance.
Drives the bulk of the compression-ratio target (A→B = 0.34).

**OBS-A-011 [Reading speed]** *(raw A, chunk 1, ≈25% mark)*

> заставляют переживать, страдать, мучиться и так далее, и так далее, и так далее.

Triple-trail filler — chained "и так далее" after a list of three
synonyms. Spoken-delivery closure that signals "list ends here."
Carries no extra item beyond what was enumerated. Pattern recurs
≥ 4× across A; B (written) drops it entirely. Confirmed
single-direction air.

**OBS-A-012 [Reading speed]** *(raw A, chunk 1, ≈30% mark)*

> то есть это эмпатические отношения, эмпатические отношения.

Word-doubling. Spoken anchoring through one-word emphatic
restatement. Carries no information beyond the first
occurrence. Recurs ≥ 6× across A on different nouns
(Интерпретация, Какие знания нам необходимы, etc.). Air —
drops in B.

**OBS-A-013 [Reading speed][Voice preservation]** *(raw A, chunk 1, ≈45% mark)*

> Все ли это? Тоже далеко не все. Потому что у нас, кроме всего этого, есть, ну, я здесь вам написал «стресс», да, но есть, значит, кризисные состояния.

Self-Q&A scaffolding combined with discourse markers ("ну",
"да", "значит") and a meta-deictic ("я здесь вам написал").
The question exists only to lift the next claim. Air, but the
boundary with form is subtle: the rhetorical question is
sometimes the *only* signal of a topic shift in spoken delivery
— S6 information-architecture step has to decide whether
section breaks survive into source.md.

**OBS-A-014 [Reading speed][Fact-check coverage]** *(raw A, chunk 1, ≈25% mark)*

> Не случайно Маск, в общем, всем обещает нам скоро чип в голову. Это стало возможным именно за счет того, что развиваются нейронауки.

Empty-intensifier appeal to authority + celebrity name-drop
("Маск… чип в голову"). The neuroscience-progress claim that
follows is real and verifiable; the Маск hook is decoration
that piggybacks plausibility on a celebrity. Drop the hook,
keep the claim, send the claim to fact-check.

**OBS-B-015 [Reading speed][Fact-check coverage]** *(raw B, in the "формула невроза" section)*

> Каждое из этих направлений, безусловно, по-своему эффективно, иначе бы соответствующие практики уже давно показали бы свою неэффективность и перестали бы преподаваться.

Effectiveness-by-popularity argument: "method X is effective
because it's still being taught." Logical air — survival in
the curriculum is not evidence of effectiveness. The structural
claim (psychotherapy schools coexist) is fine; the support
clause is the air. A fact-check pass on this would either
require evidence or downgrade the claim.

**OBS-A-016 [Transcription accuracy]** *(raw A, chunk 4, near end)*

> у нас обформируются разные психотипы

"обформируются" is a non-word — Whisper transcribed a stutter as
a fused token. Transcription artefact, not Курпатов's own
diction. Air with respect to wiki content; relevant for the
transcription-accuracy capability dimension since it surfaces
the rate at which Whisper produces ortho-aberrations the
condense step must absorb.

**OBS-A-017 [Reproducibility]** *(raw A, all chunks)*

(no quote — this is a structural observation about format
distribution, evidenced across the entire raw)

Raw A contains no segment-level paragraph breaks; it is one
~10K-word run of segment text. B (written конспект) has
explicit section headers ("01 ПЕРЕЖИВАНИЯ НАЧИНАЮЩЕГО
ПСИХОЛОГА"). The condense step must reconstruct paragraph
structure from semantic shifts, not from input formatting —
otherwise the same source produces different output depending
on whether Whisper happened to insert period-pause newlines.
Reproducibility from `(Dockerfile + raw)` only requires the
condense step to be deterministic against unstructured input.
**OBS-A-028 [Reading speed]** *(raw A, chunk 1, ≈8% mark)*

> какие-то депрессивные реакции, или еще что-то, что требует нашего профессионально-систематической работы

"Или еще что-то" — vague-terminator. Same family as triple-
trail filler (P1) but at the smaller scale of "list of things,
plus something". Air at the scale of phrases, not sentences.

**OBS-A-029 [Reading speed][Transcription accuracy]** *(raw A, chunk 1, ≈30% mark)*

> у нас, кроме всего этого, есть, ну, я здесь вам написал «стресс», да, но есть, значит, кризисные состояния

Discourse-marker stutter overlay ("ну", "да", "значит" all
in one clause) + meta-deictic ("я здесь вам написал"). Three
fillers in 18 words. Air, with a transcription-side
contribution: this density of disfluencies is what makes
Whisper output noisy.

**OBS-A-030 [Reading speed]** *(raw A, chunk 1, near end of #5 community)*

> на созвонах вместе участвовать все понимаете что вы учитесь

Vague metacommentary on the act of participating ("все
понимаете что вы учитесь") that contains no information
beyond "students learn." Air with second-order signal —
agent should detect that "все понимаете что" introduces a
tautological claim that can be cut.

**OBS-cross-031 [Dedup correctness][Concept-graph quality]** *(cross-source: raw A + raw C)*

> вот эти три базовые потребности, потребность в самозащите, в выживании, потребность в социальном взаимодействии

(raw A, chunk 4) — and raw C separately introduces the same
three-base-needs taxonomy:

> насколько гармонично и полно наши базовые потребности реализуются

(raw C). The concept *базовые потребности* appears across
both raws as the load-bearing taxonomy. Wiki must dedup the
concept article (one slug, two `touched_by`); the *first
introduction* in the source order (A → C) is `NEW`, the
second is `REPEATED (from: <A's slug>)`. Critical Dedup-
correctness case for a multi-module compile.

**OBS-cross-032 [Dedup correctness]** *(cross-source: raws A + C + D)*

> Это им движет инстинкт самосохранения?

(raw A, chunk 4) — and the same concept reappears in raw C:

> вот эта часть, это больше за инстинкт самосохранения отвечает

— and again in raw D:

> делать уже социальное, потом инстинкт самосохранения вида рассказывать

Three-raw recurrence of *инстинкт самосохранения*. The wiki's
dedup pass must keep one concept article and three
`Contributions by source` entries; getting this wrong
duplicates the slug N times across the corpus (the K1 v1
failure mode that motivated the dedup capability).

**OBS-meta-033 [Requirement traceability][Fact-check coverage]** *(meta: across all 5 raws)*

> Стресс — это, если опираться на определение, которое дал ему автор теории Ганс Селье

(raw A, paraphrasing Selye explicitly — see OBS-A-001) —
versus unattributed branded claims like:

> Говорить об эффективности данной технологии мы можем не только благодаря результатам тысяч наших благодарных студентов

(raw B, OBS-B-015's neighbour). The corpus carries two
classes of claim: those with explicit external attribution
(Selye, Эпиктет, Адлер, Карл Роджерс, Карен Хоурни, Эрик
Фромм, Маск, Фрейд appear by name) and those with self-
attribution only (Курпатов's own framings, branded methods,
"тысяч учеников" assertions). The wiki's `R-NN` requirements
should distinguish: external-attribution claims roll up to
*Fact-check coverage* (verifiable); self-attribution claims
roll up to *Voice preservation* (signature). Mixing them is
the trap that makes a wiki feel authoritative when it isn't.


## Coverage map

Distinct capability dimensions exercised across observations
(T-WP-01 acceptance #5 requires ≥ 6 of 8):

| Dimension                  | Observations |
|----------------------------|--------------|
| **Voice preservation**     | OBS-A-002, OBS-A-006, OBS-A-007, OBS-A-008, OBS-A-009, OBS-A-013, OBS-D-010 |
| **Reading speed**          | OBS-A-011, OBS-A-012, OBS-A-013, OBS-A-014, OBS-B-015 |
| **Concept-graph quality**  | OBS-A-001, OBS-A-002, OBS-A-003, OBS-B-004, OBS-C-005, OBS-A-008 |
| **Fact-check coverage**    | OBS-A-014, OBS-B-015 |
| **Transcription accuracy** | OBS-A-016 |
| **Reproducibility**        | OBS-A-017 |
| **Dedup correctness**      | (no observation yet — coverage hole; revisit after a multi-source S2 pass that cross-references slugs across A and C) |
| **Requirement traceability** | (this file itself; no in-corpus observation) |

Distinct dimensions covered: **6 of 8** (Voice preservation,
Reading speed, Concept-graph quality, Fact-check coverage,
Transcription accuracy, Reproducibility). Meets the T-WP-01
threshold.

## Per-bucket count

- **Substance**: 5 observations (OBS-A-001, OBS-A-002, OBS-A-003,
  OBS-B-004, OBS-C-005). Threshold ≥ 3 — pass.
- **Form**: 5 observations (OBS-A-006, OBS-A-007, OBS-A-008,
  OBS-A-009, OBS-D-010). Threshold ≥ 3 — pass.
- **Air**: 7 observations (OBS-A-011, OBS-A-012, OBS-A-013,
  OBS-A-014, OBS-B-015, OBS-A-016, OBS-A-017). Threshold ≥ 3 —
  pass.

## Boundaries (S2 stop-line)

The Wiki PM role stopped here per T-WP-01 instructions. Output:

- **No** R-NN rows have been written into
  [`/phase-requirements-management/catalog.md`](../../../phase-requirements-management/catalog.md)
  (S7 is out of scope for this run).
- **No** files under
  [`/phase-c-information-systems-architecture/application-architecture/wiki-bench/`](../../../phase-c-information-systems-architecture/application-architecture/wiki-bench/),
  the wiki sibling repo's `prompts/` or `data/`, or any forge
  prompt/grader has been modified.

S3–S7 are queued; they consume the observations above by ID.
