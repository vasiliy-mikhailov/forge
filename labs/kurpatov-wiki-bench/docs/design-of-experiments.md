# Experiment Log — kurpatov-wiki-compiler benchmarking

Lean validation board. Документ живой: §2 переоценивается после каждого
заполнения строки в §4.

## 1. Strategy

### 1.1 Current State (Baseline)

- Opus 4.6 проходит Pass-условие (§5) на всех 7 source модуля 005.
  Стоимость: дорого по $/token и латентности; гарантированный исход.
  Эталонная ветка: `bench/2026-04-25-claude-opus-4-6-cowork`, commit `a8b8c2a`.
- Локальный compiler (vLLM на RTX 6000 Pro Blackwell, 96 GB) с
  Qwen3.6-27B в двух квантах — `cyankiwi/Qwen3.6-27B-AWQ-INT4` и
  `Qwen/Qwen3.6-27B-FP8` — детерминированно падает на ~turn 26 с
  `Error validating tool 'file_editor': Unterminated string`. Триггер:
  модель отдаёт ~40 KB Cyrillic article body одним вызовом
  `file_editor.create`, JSON `tool_call.arguments` обрывается в середине
  строки.
- Стоимость одного полного цикла: ~10 мин compose-up + ~5–20 мин агента.
  Веса хранятся в `${STORAGE_ROOT}/shared/models/`, ~25–30 GB на модель.

### 1.2 Target Condition

- ≥ 1 open-weight self-hosted модель воспроизводимо проходит Pass-условие
  (§5) на source 000 за < 60 мин wall на одном RTX 6000 Pro.
- Стоимость прогона source ≤ $0.01 (электричество + amortized GPU).
- На горизонте — батарея по всему модулю 005 + регрессионный тест при
  каждом swap'е модели.

### 1.3 The Path (the bet)

> **Проблема — в skill'е, не в модели.** Skill v1 написан под frontier-
> модели, которые держат 65K coherence и сериализуют огромные JSON args.
> Open-weight 24–49B-классу нужен skill v2 — инкрементальный workflow
> с args ≤ 8 KB на каждом tool-call.

Если ставка верна → cheap self-hosted бенчмарк, без правок compiler'а.
Если ложна → надо подниматься к 70B+ классу (дороже железо, медленнее).
Все остальные гипотезы — попытки опровергнуть The Path или найти ещё
дешёвый сценарий.

## 2. Hypothesis Backlog

Шкалы 1–5.
**Risk** = насколько разрушит The Path, если гипотеза ОКАЖЕТСЯ ложной (5 = крах стратегии).
**Cost** = ресурсы на проверку (1 = дёшево, 5 = дорого).
**Confidence** = текущая уверенность что гипотеза ИСТИННА (1 = почти не верим, 5 = почти убеждены).
**Score** = `Risk × (6 − Confidence) / Cost` — приоритет следующего теста.
Идём в порядке убывания Score.

| ID  | IF–THEN–BECAUSE                                                                                                                                                               | Risk | Cost | Conf | Score | Status                  |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ---- | ---- | ----- | ----------------------- |
| H1  | IF причина в community-AWQ-кванте, THEN official FP8 пройдёт, BECAUSE багов нет в офф-релизе.                                                                                 | 1    | 1    | 1    | —     | ✗ REFUTED 2026-04-25    |
| H8  | IF 65K контекст близок к coherence-границе модели, THEN trimmed transcript (30 KB вместо 50 KB) даст пройти, BECAUSE уменьшаем нагрузку на attention.                         | 2    | 1    | 2    | **8** | open ← **next**         |
| H2  | IF баг — в семействе Qwen3.6, THEN Qwen3.5-27B и Qwen3-32B пройдут шаг file_editor.create, BECAUSE в Qwen3.x не наблюдалось таких сообщений.                                  | 3    | 2    | 2    | 6     | open                    |
| H3  | IF max_completion_tokens обрезает completion в середине строки, THEN bump до 32 768 устранит краш, BECAUSE длинный body упирается в дефолтный лимит.                          | 1    | 1    | 2    | 4     | open                    |
| H4  | IF парсер qwen3_xml ломает Cyrillic args, THEN swap на hermes устранит краш, BECAUSE hermes старее и обкатанее на Cyrillic.                                                   | 1    | 1    | 2    | 4     | open                    |
| H6  | (THE BET) IF skill переписать на инкремент (stub + section-by-section, args ≤ 8 KB), THEN qwen3.6-27b-fp8 пройдёт Pass, BECAUSE корень — JSON-тяжесть, а не reasoning.        | 5    | 3    | 4    | 3.3   | open (защищаем как путь)|
| H5  | IF задача в skill v1 недоступна всему dense 24–49B классу, THEN ни одна из 5 моделей не пройдёт, BECAUSE общая слабость сериализации длинных JSON.                            | 4    | 4    | 3    | 3     | open (composite of E3..E9) |
| H7  | IF размер модели — пороговый фактор, THEN llama-3.3-70b-nvfp4 пройдёт без правки skill'а, BECAUSE у 70B хватает coherence на 65K.                                             | 2    | 2    | 3    | 3     | open                    |

### 2.1 Selected next test

**H8** (Score = 8). Самая дешёвая среди тех, что могут реально опровергнуть
The Path. Если H8 истинна — корень в context-budget'е, а не в skill'е, и
тогда H6 не нужен (мы выиграли без переписывания skill'а). Если H8 ложна
— получаем твёрдое доказательство: «контекст ни при чём», и со спокойной
душой можем вкладываться в H6.

Параллельно следующими в очереди — H3 и H4 (тоже cheap, тоже не требуют
новых весов). После них уже принимаем решение, идти ли в H2 (другие
Qwen) или сразу в H6 (skill v2).

## 3. Test Card — H8: context starvation

### 3.1 Гипотеза

Если усечь transcript source 000 с ~50 KB до ~30 KB (первые 1000 из 1614
сегментов), то Qwen3.6-27B-FP8 при том же skill v1 пройдёт момент
`file_editor.create source 000.md` без `Unterminated string` и доведёт
source-статью до commit'а.

### 3.2 Критерий фальсифицируемости (зафиксирован ДО теста)

H8 опровергнута, если в `events.jsonl` появляется
`AgentErrorEvent` или `ConversationErrorEvent` с подстрокой
`Unterminated string` или `unparseable JSON` на любом
`file_editor` вызове до момента `git commit`.

Любой иной класс ошибки → не falsify, а новые данные → пересмотреть
backlog (возможна новая гипотеза H9+).

### 3.3 Метрика успеха (threshold)

| исход                                                                              | вердикт          |
| ---------------------------------------------------------------------------------- | ---------------- |
| модель доходит до `git commit` source 000 без AgentErrorEvent                      | H8 PASS          |
| модель создаёт source.md, но падает позже (на концептах, на index)                 | H8 partially PASS — invalidates "JSON-truncation объясняет всё"; новая гипотеза |
| тот же `Unterminated string` на каком-то file_editor вызове                        | H8 FAIL          |

### 3.4 Дизайн теста

1. В `labs/kurpatov-wiki-bench/run.sh` добавить env-флаг
   `TRANSCRIPT_TRIM_SEGMENTS=N`. Если задан — внутри bench-контейнера
   подменять `/workspace/raw/.../raw.json` на копию с первыми N
   сегментами.
2. Запустить:
   `TRANSCRIPT_TRIM_SEGMENTS=1000 ./run-battery.sh qwen3.6-27b-fp8`
3. Артефакты пишутся в
   `experiments/<run_id>-h8-trim1000/`. Run_id берёт
   суффикс `-h8-trim1000` для отличения от baseline.
4. Wall-clock budget: ≤ 30 минут (compose уже поднят, веса в кэше).

### 3.5 Стоимость

~5 мин патчить `run.sh` + ~15 мин agent. GPU: один цикл Blackwell.
Не требуется новых весов, не требуется правки compose. Risk to revert: 0.

## 4. Learning Log

| date       | run_id                              | hypothesis | result                                                                  | insight                                                                                | decision                          |
| ---------- | ----------------------------------- | ---------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------- |
| 2026-04-25 | 2026-04-25-200224-qwen3.6-27b-fp8   | H1         | `Unterminated string` на turn 26, идентично AWQ-INT4                    | Проблема не в кванте; общая для Qwen3.6 27B независимо от формата весов                | REFUTE H1; persevere with The Path |
| _next_     | (h8-trim1000)                       | H8         | _pending_                                                               |                                                                                        |                                   |

## 5. Pass condition (referenced from §1)

Pass на одном source (e.g. 000):

- `data/sources/<course>/<module>/000 *.md` ≥ 200 строк, валидный
  frontmatter (`slug`, `course`, `module`, `concepts_touched[]`,
  `concepts_introduced[]`, `fact_check_performed`).
- ≥ 30 концепт-статей в `data/concepts/<slug>.md`, у каждой
  `## Definition`.
- `concept-index.json` обновлён: новая запись в `processed_sources` +
  пополнен dict `concepts`.
- Один коммит на ветке `bench/<date>-<model>`, сообщение `source: <slug>`.
- `git push origin <branch>` зелёный.
- В `events.jsonl` нет `AgentErrorEvent` и нет `ConversationErrorEvent`.

## 6. Принципы работы с этим документом

- §2 (Backlog) переоценивается после каждой записи в §4 (Learning Log).
  Если ранее non-tested гипотеза стала более рискованной — поднимаем её
  Risk; если новые данные снизили Cost (например, появился готовый
  тулинг) — снижаем.
- §3 (Test Card) переписывается под новую выбранную гипотезу. Старые
  Test Card'ы не хранятся — их след в §4 как «design выбранного
  эксперимента».
- Решение pivot/persevere фиксируется в колонке `decision` §4. Pivot ⇒
  правка §1.3 (The Path).

## 7. История ревизий

| ver | дата       | что изменилось                                                                              |
| --- | ---------- | ------------------------------------------------------------------------------------------- |
| 0.1 | 2026-04-25 | initial draft (DoE с factorial-style матрицей; 13 ячеек; superseded)                        |
| 0.2 | 2026-04-25 | переформат в Lean Validation Board: Strategy / Backlog / Test Card / Learning Log; H8 next  |
