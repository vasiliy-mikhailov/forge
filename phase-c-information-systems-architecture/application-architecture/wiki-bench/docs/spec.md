# Experiment Methodology — wiki-compiler

Этот документ описывает **подход**, как мы организуем эксперименты
в этой лаборатории. Конкретных гипотез и метрик здесь нет: они
лежат в [`backlog.md`](backlog.md) (список идей с ICE-скорами) и в
`experiments/<id>.md` (детальный спек активной гипотезы).

## 1. What we're improving

### 1.1 Главное: **skill**

Лаборатория улучшает не модель и не инференс-движок, а **skill** —
playbook (markdown-инструкции), который агент читает и выполняет
для компиляции raw-транскриптов в wiki-статьи. Skill живёт в
[`kurpatov-wiki-wiki/skills/benchmark/`](https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/tree/main/skills/benchmark)
и определяет:

- **Workflow**: клонировать оба репо (raw + wiki), завести bench-ветку,
  для каждого source — прочесть prompts, обработать transcript,
  написать source-статью, написать концепт-статьи, обновить
  `concept-index.json`, atomic commit + push.
- **Output формат**: frontmatter schema (`slug`, `course`, `module`,
  `concepts_touched[]`, `concepts_introduced[]`, `fact_check_performed`),
  секции `TL;DR` / `Claims — provenance and fact-check` / `New ideas
  (verified)` / `All ideas` / `Notes`, провенанс-маркеры (`NEW`,
  `REPEATED (from: ...)`, `CONTRADICTS EARLIER (in: ...)`, `CONTRADICTS
  FACTS`).
- **Tool repertoire**: какие OpenHands tools агент использует
  (`file_editor`, `terminal`, `task_tracker`, `web_search`), и как они
  обёрнуты в инструкциях skill'а.
- **Pass condition**: что считается «source готов» (см. §6).

### 1.2 Окружение skill'а

Skill не работает в вакууме. Его выполняет агент в bench-харнессе:

```
┌────────────────────────────────────────────────────────────┐
│                Bench Harness                               │
│  (forge/phase-c-information-systems-architecture/application-architecture/wiki-bench)                          │
│                                                            │
│  Sandboxed Docker (python:3.12-slim + git/jq/curl),        │
│  bind-mount только /runs/current,                          │
│  GitHub auth через GITHUB_TOKEN,                           │
│  entry point: bin/openhands CLI 1.17.0                     │
│                                                            │
│   ┌──────────────────────────────────────────────────┐     │
│   │       OpenHands SDK Agent                        │     │
│   │       (LLMConfig: max_tok, temp, tools-spec)     │     │
│   │                                                  │     │
│   │   reads ─→ SKILL.md ─────┐                       │     │
│   │                          ↓                       │     │
│   │      tool calls ←── interpreter (model brain)    │     │
│   │      JSON tool args                              │     │
│   │      ↓                                           │     │
│   │   ┌──────────────────────────────────────────┐   │     │
│   │   │      vLLM compiler                       │   │     │
│   │   │  (forge/phase-c-information-systems-architecture/application-architecture/wiki-compiler)     │   │     │
│   │   │   model: Qwen3.6-27B-FP8 / Llama-70B     │   │     │
│   │   │   parser: qwen3_xml / hermes             │   │     │
│   │   │   max_model_len: 65536                   │   │     │
│   │   └──────────────────────────────────────────┘   │     │
│   └──────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────┘

inputs:  kurpatov-wiki-raw   (Cyrillic JSON transcripts)
outputs: kurpatov-wiki-wiki  (markdown sources + concepts + index,
                              на ветке bench/<date>-<model>)
```

- **Skill** — то, что мы шлифуем; финальный артефакт, который шипуется
  пользователям-агентам.
- **Harness** (`phase-c-information-systems-architecture/application-architecture/wiki-bench/`) — runtime для skill'а: то,
  что запускает агента, мерит, ловит ошибки, складывает артефакты.
  Стабилизировался после refactor step 5; правится реже.
- **Model + serving** (`phase-c-information-systems-architecture/application-architecture/wiki-compiler/`) — third-party
  вес + vLLM. Не «улучшаем», а выбираем подходящую под текущий skill.
  Параметры serving'а (vLLM флаги) — улучшаем.

### 1.3 Main thesis (pivoted twice — final 2026-04-25 после A8)

**Хронология ставок на этот run:**

1. **Ставка v0** (initial): «skill v1 написан под Opus, open-weight
   24-49B классу не по зубам — переписать skill».
2. **Ставка v1** (после F1 microbench): «модель в порядке (L\*≥49KB),
   виноват max_completion_tokens cap в OpenHands». D-cluster понижен.
3. **Ставка v2 (current, после A8)**: **виноват `max_model_len` (KV-budget
   контекста), не max_completion_tokens.**

**A8 эксперимент 2026-04-25**: бампнули `max_model_len: 65536 → 131072`
(YaRN factor 2.0→4.0). Тот же T3 на том же Qwen3.6-27B-FP8, тот же
skill v1 — **проходит**: source 000 успешно создан, 6 концептов созданы,
concept-index обновлён, commit+push на `bench/2026-04-25-qwen3.6-27b-fp8`
зелёный. **Pass partial** (source 136 строк vs Opus 216, концептов 6
vs 32 — quality regression), но JSON-truncation crash **полностью
устранён**.

**Корень**: T3 prompt (~50K input tokens: skill+CLAUDE+prompts+
transcript+turn history) + агентский output для source.md (~16K tokens
Cyrillic body) = ~66K. С `max_model_len=65536` — buffer 0; модель
обрывается. С `max_model_len=131072` — буфер 65K, всё помещается.

**Следствия для backlog:**
- **A1 (max_tokens bump)**: Confidence ↓↓. 128K сам по себе хватает,
  max_completion_tokens default OpenHands не ограничивает. Можно не трогать.
- **A4 (guided JSON), A2 (parser swap), A3 (tool_choice)** — defense-in-depth.
- **D-cluster (skill v2/v3/v4)** — теперь чисто quality-улучшение
  (для повышения числа концептов и длины source), не нужны для pass.
- **B-cluster (other models)** — теперь имеет смысл разворачивать всю
  батарею: с 128K контекстом любая dense 24-49B должна пройти.
- **F4 (GPT-4o pairwise judge)** — поднимается, потому что вопрос
  смещается с «работает или нет» на «насколько хорошо vs Opus».

The Big Bet → **«любая dense 24-49B модель + 128K context + skill v1
проходит T3, разница только в quality»**. Falsifier: при батарее
gpt-oss-20b / Devstral-Small-2-24B / Mistral-Small-3.2-24B / Nemotron-
Super-49B-v1.5 / Llama-3.3-70B хоть одна не проходит на этой
конфигурации.

## 2. North Star (target condition)

- ≥ 1 open-weight self-hosted модель воспроизводимо проходит **Pass**
  (§6) на T3 (полный source) за ≤ 60 мин wall на одном RTX 6000 Pro
  Blackwell, **с улучшенным skill v2**.
- Cost per source ≤ \$0.01 (электричество + amortized GPU).
- На T4 (полный модуль 005, 7 source) — ≥ 80% pass rate.
- Skill v2 публикуется в `kurpatov-wiki-wiki/skills/benchmark/` как
  стабильная замена v1.

## 3. Backlog rules

### 3.1 ICE scoring

`ICE = I × C × E`, диапазон 1–1000. Каждое измерение 1–10:

- **Impact** — насколько приближает к North Star, если сработает.
  Здесь главный фокус: «насколько эта гипотеза улучшит skill либо
  снимет необходимость его улучшать».
- **Confidence** — уверенность, что сработает (статьи, прецеденты,
  интуиция). *Низкий C ≠ плохо*: «низкая confidence + высокий impact +
  лёгкая проверка» — типовой профиль рискованной ставки.
- **Ease** — 1 = недели работы; 10 = минуты конфига.

Берём top-3 по ICE как кандидатов на следующий детальный спек.

### 3.2 Lifecycle идеи

```
backlog → triaged → spec → running → done | refuted | skip
```

- **backlog** — записано, не оценено или оценено низко.
- **triaged** — оценили, в топе, ждёт написания experiments/<id>.md.
- **spec** — детальный спек написан, готов к запуску.
- **running** — эксперимент идёт, появилась запись в Execution Log спека.
- **done** — завершён, Post-Mortem заполнен; результат влияет на ICE
  других идей.
- **refuted** — гипотеза опровергнута экспериментом.
- **skip** — технически невозможно (модели нет на HF, нет железа).

### 3.3 Когда пишется детальный спек

Только для гипотез, которые запускаем **в ближайшие 48 часов**.
Это правило защищает от писанины — из 30 идей в работу обычно идут 2–3.

### 3.4 Когда переоцениваем backlog

После каждого `done`/`refuted` (Post-Mortem заполнен). Раз в неделю —
полный triage всех `backlog` строк.

## 4. Test set tiers (scaling laws)

Самые рискованные гипотезы проверяются на малых масштабах. Гипотеза
**не идёт на T(k+1), пока не прошла на T(k)**. Исключение: первая
запись по новой модели сразу делает T1+T3 baseline.

| tier | название               | объём                                                      | cost/run | для каких гипотез          |
| ---- | ---------------------- | ---------------------------------------------------------- | -------- | -------------------------- |
| T1   | microbench-cyrillic    | синтетика, 9 длин × 10 trials = 90 completion-вызовов      | ~10 мин  | конфиг-tweaks, model swaps |
| T2   | ablated source 000     | 1 source, transcript усечён до 30 KB                       | ~25 мин  | smoke skill v2/v3          |
| T3   | full source 000        | 1 source, full transcript (50 KB) — нынешний Pass          | ~30 мин  | финальный candidate test   |
| T4   | full module 005        | 7 sources, инкрементальный pipeline                        | ~3–4 ч   | окончательный winner       |

## 5. Standard guardrails

Метрики, которые не должны деградировать **независимо от гипотезы**.
Спек активного эксперимента может добавить свои.

- **TPS** (output tokens / sec) на Blackwell ≥ 30 t/s.
- **Latency p95** на одиночный completion ≤ 5 сек для типового
  payload (≤ 4 KB tool args).
- **VRAM** ≤ 80 GB из 96 GB Blackwell — запас на параллельный rl-2048 lab.
- **Determinism**: temperature=0 → одинаковый prompt даёт sha256-
  совпадающий output между запусками. Если ломается — проблема
  изоляции/инфры, не модели.
- **Skill quality regression**: при правке skill'а — диффер `summary.json`
  по полям `claims_count`, `concepts_introduced`, `fact_check_performed`
  относительно Opus baseline. Деградация > 20% по любому полю — fail.

## 6. Pass conditions per tier

### T1 (microbench)
Зависит от конкретной гипотезы. Базовый паттерн: `pass-rate ≥ 0.95`
на N=10 trials в каждой ячейке matrix'а.

### T2 / T3 (single-source full pipeline)
- `data/sources/<course>/<module>/000 *.md` ≥ 200 строк, валидный
  frontmatter (`slug`, `course`, `module`, `concepts_touched[]`,
  `concepts_introduced[]`, `fact_check_performed`).
- ≥ 30 концепт-статей в `data/concepts/<slug>.md`, у каждой
  `## Definition`.
- `concept-index.json` обновлён.
- Один коммит на ветке `bench/<date>-<model>`, сообщение `source: <slug>`.
- `git push origin <branch>` зелёный.
- В `events.jsonl` нет `AgentErrorEvent` и нет `ConversationErrorEvent`.

### T4 (full module)
≥ 80% source'ов модуля проходят T3 condition (то есть ≥ 6 из 7).

## 7. Falsifiability principle

Каждый детальный спек обязан содержать секцию **Falsifiability Criteria**,
зафиксированную **до запуска**. Это защита от когнитивного искажения,
когда исследователь пытается «интерпретировать» провальный результат
как «ну, почти получилось».

Формат: «гипотеза опровергнута, если выполняется хотя бы одно из:
[конкретные численные / pattern-based условия]».

Любой исход, не подпадающий под falsifier — **новые данные**, не
подтверждение гипотезы. Решение pivot/scale принимается в Post-Mortem.

## 8. Hypothesis categories: где живёт изменение

Каждая гипотеза в `backlog.md` падает в одну из категорий ниже —
определяющую, **что именно меняем** в системе из §1.2.

| cat   | где живёт изменение                                       | пример идеи                              | когда полезно                                    |
| ----- | --------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------ |
| A     | vLLM флаги / OpenHands LLMConfig                          | swap parser, bump max_tok, guided JSON   | дёшево; снимает конфигурационные косяки          |
| B     | другая модель, тот же skill v1                            | Qwen3.5 вместо Qwen3.6, Llama-70B        | определяет, виноват ли конкретный вес            |
| C     | другой inference engine                                   | SGLang вместо vLLM, llama.cpp GGUF       | проверяет, не баг ли это движка                  |
| **D** | **skill itself** (markdown в kurpatov-wiki-wiki/skills)   | **incremental write, terminal heredoc**  | **THE BET — финальный deliverable лаборатории**  |
| E     | preprocessing данных до agent run                         | trim transcript, pre-summarize           | дёшево уменьшает нагрузку на skill+model         |
| F     | evals / metrics (instrumentation)                         | microbench L*, GPT-4o pairwise judge     | строит axes для сравнения остальных гипотез      |
| G     | infrastructure (compose, GPU layout)                      | dual-GPU TP, speculative decoding        | расширяет потолок размера модели                 |

**D — это the bet.** Skill v2 — конечный артефакт, который мы шипуем
в `kurpatov-wiki-wiki/skills/benchmark/SKILL.md`. Все остальные
категории — это либо инструментация (F), либо дешёвые ablations,
проверяющие «можно ли обойтись без правки skill'а» (A/B/C/E/G).

Если A/B/C/E/G **закрываются** до того, как мы успеваем потрогать
D — отлично, мы выиграли дёшево. Если все провалятся — у нас твёрдое
обоснование инвестировать в D.

## 9. Experiment file template

`experiments/<id>.md` (где `<id>` — стабильный идентификатор из backlog,
например `F1`, `D2`, `B3`):

```
# <ID> — <short title>
## Hypothesis (IF–THEN–BECAUSE)
## Methodology
## Falsifiability criteria
## Parameters (Fixed / Variables / DoE matrix)
## Evaluation
  ### Primary metric
  ### Guardrail metrics (delta to spec.md §5)
  ### Test set
## Execution log
  table: run_id | date | status | artifact link
## Post-Mortem & Insights
  what happened | why | next step (pivot/scale)
```

После закрытия (Post-Mortem заполнен) файл остаётся в `experiments/`
как «памятник истории» — в `backlog.md` строка получает статус `done`
и колонка Spec продолжает на него ссылаться.

## 10. Artifact paths

Все артефакты прогонов кладутся в `${STORAGE_ROOT}/labs/wiki-bench/`:

- T1: `evals/microbench/<date>-<exp_id>-<model>.csv`
- T2/T3: `experiments/<run_id>/` (events.jsonl, summary.json,
  vllm-snapshot-{start,end}.json)
- T4: `battery-runs/<date>.log` + per-experiment subdirs

В `experiments/<id>.md` Execution Log колонка `artifact` обязана давать
работающий путь до того, как переходим к следующей гипотезе.

## 11. Document conventions

- ID идеи стабильный: `A1`, `B3`, `F1` — даже после refute не переиспользуется.
- Если гипотеза при «pivot»'е принципиально меняется — заводится новая
  идея с новым ID, старая остаётся как `refuted`.
- `spec.md` (этот файл) меняется только при изменении методологии или
  переосмыслении §1 (что улучшаем). Не трогаем при добавлении/закрытии
  конкретных экспериментов.
- `backlog.md` — точка входа: оттуда видим, что в работе и что в очереди.

## 12. Ревизии методологии

| ver | дата       | что изменилось                                                                                                                                            |
| --- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0.1 | 2026-04-25 | factorial-DoE-style 13-cell matrix как «спек»                                                                                                            |
| 0.2 | 2026-04-25 | Lean Validation Board                                                                                                                                     |
| 0.3 | 2026-04-25 | AI-lab format: Context+North Star / Backlog / Design / Evals / Execution / Post-Mortem; tiers T1..T4                                                     |
| 0.4 | 2026-04-25 | split: backlog → backlog.md; spec.md → методология; детальный спек активной гипотезы → experiments/<id>.md                                              |
| 0.5 | 2026-04-25 | добавлено §1 «What we're improving» — skill как главный артефакт под улучшением; §8 категории гипотез по «где живёт изменение»; D помечен как THE BET   |


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain (OKRs) inherited from the lab's AGENTS.md.
