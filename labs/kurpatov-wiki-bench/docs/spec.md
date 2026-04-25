# Experiment Methodology — kurpatov-wiki-compiler

Этот документ описывает **подход**, как мы организуем эксперименты
в этой лаборатории. Конкретных гипотез и метрик здесь нет: они
лежат в [`backlog.md`](backlog.md) (список идей с ICE-скорами) и в
`experiments/<id>.md` (детальный спек активной гипотезы).

## 1. Mission

`kurpatov-wiki-compiler` — пайплайн «raw-транскрипт → wiki-статья +
концепты + atomic commit». Эталон поведения задан Opus 4.6. Цель —
найти cheap self-hosted замену, которая воспроизводимо проходит то
же качество.

## 2. North Star (target condition)

- ≥ 1 open-weight self-hosted модель воспроизводимо проходит **Pass**
  на T3 (полный source) за ≤ 60 мин wall на одном RTX 6000 Pro Blackwell.
- Cost per source ≤ \$0.01 (электричество + amortized GPU).
- На T4 (полный модуль 005, 7 source) — ≥ 80% pass rate.

## 3. Backlog rules

### 3.1 ICE scoring

`ICE = I × C × E`, диапазон 1–1000. Каждое измерение 1–10:

- **Impact** — насколько приближает к North Star, если сработает.
- **Confidence** — уверенность, что сработает (статьи, прецеденты,
  интуиция). *Низкий C ≠ плохо*: «низкая confidence + высокий impact +
  лёгкая проверка» — типовой профиль рискованной ставки, которую
  стоит проверять.
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

Любой исход, не подпадающий под falsifier — **новые данные**, не подтверждение
гипотезы. Решение pivot/scale принимается в Post-Mortem.

## 8. Experiment file template

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

## 9. Artifact paths

Все артефакты прогонов кладутся в `${STORAGE_ROOT}/labs/kurpatov-wiki-bench/`:

- T1: `evals/microbench/<date>-<exp_id>-<model>.csv`
- T2/T3: `experiments/<run_id>/` (events.jsonl, summary.json,
  vllm-snapshot-{start,end}.json)
- T4: `battery-runs/<date>.log` + per-experiment subdirs

В `experiments/<id>.md` Execution Log колонка `artifact` обязана давать
работающий путь до того, как переходим к следующей гипотезе.

## 10. Document conventions

- ID идеи стабильный: `A1`, `B3`, `F1` — даже после refute не переиспользуется.
- Если гипотеза при «pivot»'е принципиально меняется — заводится новая
  идея с новым ID, старая остаётся как `refuted`.
- `spec.md` (этот файл) меняется только при изменении методологии.
  Не трогаем при добавлении/закрытии конкретных экспериментов.
- `backlog.md` — точка входа: оттуда видим, что в работе и что в очереди.

## 11. Ревизии методологии

| ver | дата       | что изменилось                                                                                                |
| --- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| 0.1 | 2026-04-25 | factorial-DoE-style 13-cell matrix как «спек»                                                                |
| 0.2 | 2026-04-25 | Lean Validation Board                                                                                         |
| 0.3 | 2026-04-25 | AI-lab format: Context+North Star / Backlog / Design / Evals / Execution / Post-Mortem; tiers T1..T4         |
| 0.4 | 2026-04-25 | split: backlog → backlog.md; spec.md → методология; детальный спек активной гипотезы → experiments/<id>.md   |
