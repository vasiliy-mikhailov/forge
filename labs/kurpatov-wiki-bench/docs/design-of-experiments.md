# Design of Experiments — kurpatov-wiki-compiler

Цель документа — задать фальсифицируемые гипотезы и план экспериментов
для бенчмарка open-weight моделей на задаче «raw-транскрипт → wiki-статья
+ концепты + atomic commit». Пишется после двух подряд провалов
Qwen3.6-27B (AWQ-INT4 community и FP8 official) с одной и той же
ошибкой `Error validating tool 'file_editor': Unterminated string`.

## 1. Цель и определение успеха

**Pass-условие** (для одиночного source 000):

- `data/sources/<course>/<module>/000 *.md` ≥ 200 строк, валидный frontmatter
  (`slug`, `course`, `module`, `concepts_touched`, `concepts_introduced`,
  `fact_check_performed`).
- ≥ 30 концепт-статей в `data/concepts/<slug>.md`, каждая с `## Definition`.
- `concept-index.json` обновлён: `processed_sources` += {slug, processed_at,
  concepts_touched[], concepts_introduced[]}; `concepts` dict пополнен.
- Один коммит на ветке `bench/<date>-<model>` с сообщением `source: <slug>`.
- `git push origin <branch>` вернул success.
- В `events.jsonl` нет `AgentErrorEvent` и нет `ConversationErrorEvent`.

**Эталон** — `bench/2026-04-25-claude-opus-4-6-cowork` (commit `a8b8c2a`),
содержит 7 source-статей + 59 концептов. Опус прошёл; для open-weight
этой планки ещё не достигал никто.

## 2. Контекст и наблюдения

| run                                      | модель                          | turn-ов | финал                                             |
| ---------------------------------------- | ------------------------------- | ------- | ------------------------------------------------- |
| `2026-04-22-...-qwen3.6-27b` (1)         | cyankiwi/Qwen3.6-27B-AWQ-INT4   | ~25     | JSON-truncation в file_editor.create source 000   |
| `2026-04-23-...-qwen3.6-27b` (2)         | то же (после patch'а skill'а)   | ~28     | то же (на длинном Cyrillic file_text)             |
| `2026-04-25-200224-qwen3.6-27b-fp8` (3)  | Qwen/Qwen3.6-27B-FP8 (official) | 26      | то же `Unterminated string starting at char 285`  |

Поломка детерминирована: модель доходит до момента «писать source-статью
целиком одним вызовом `file_editor.create`», начинает сериализовать
40-килобайтный body со многими кириллическими строками внутри JSON
`tool_call.arguments`, и обрывает в середине строки.

## 3. Falsifiable hypotheses

Каждая гипотеза заявлена как предсказание + что её опровергает + какой
эксперимент её проверяет. Если гипотеза выживает один цикл — она не
подтверждена, она просто ещё не опровергнута.

### H1 — community quant artifact (REFUTED)

> «Краш — артефакт community-AWQ-INT4 квантизации; на official FP8 баг
> исчезает.»

- Predict: Qwen3.6-27B-FP8 завершает source 000.
- Falsifier: FP8 падает с такой же `Unterminated string`.
- Status: **REFUTED** в run (3) — FP8 падает идентично AWQ-INT4. Корень не в квантизации.

### H2 — Qwen3.6 family-specific tool-mode bug

> «Дефект сериализации длинных Cyrillic-строк внутри JSON tool_call.arguments
> специфичен для семейства Qwen3.6 (новая архитектура GDN attention,
> новая instruct-разметка). Прошлые поколения Qwen3.x не падают.»

- Predict: Qwen3.5-27B-FP8 и Qwen3-32B-FP8, при тех же parser/skill, доходят
  хотя бы до этапа «write source 000» без `Unterminated string` на том же шаге.
- Falsifier: одна из них падает с такой же ошибкой.
- Experiment: **E2** (qwen3.5-27b-fp8), **E3** (qwen3-32b-fp8).
- If TRUE: проблема в самой Qwen3.6 — fix only by upstream; временно использовать Qwen3.x.
- If FALSE: семейство ни при чём → больше веса H4 / H6 / H8.

### H3 — output token cap truncates JSON mid-string

> «vLLM или OpenHands дефолтно обрезает completion до N токенов; модель
> успевает выдать `{"command":"create","path":"...","file_text":"...`
> и упирается в лимит, отдавая невалидный JSON.»

- Predict: bumping `max_completion_tokens` до 32K (или явно `32768`) в
  OpenHands `LLMConfig` устраняет краш на той же модели.
- Falsifier: та же ошибка с увеличенным лимитом; либо stop_reason ≠ `length`
  в события до краша.
- Experiment: **E5** — qwen3.6-27b-fp8 + max_completion_tokens=32768.
- If TRUE: тривиальный фикс (правка bench/run.sh); открывает дорогу всему
  семейству Qwen3.6.
- If FALSE: размер ответа ни при чём.

### H4 — qwen3_xml parser bug

> «Парсер `qwen3_xml` неправильно интерпретирует или не закрывает JSON-args
> при наличии длинного Cyrillic-текста с экранированными `\\n`. На hermes-парсере
> та же модель пишет валидный JSON.»

- Predict: qwen3.6-27b-fp8 + `--tool-call-parser hermes --reasoning-parser deepseek_r1`
  (или auto) проходит шаг создания source-файла.
- Falsifier: с hermes-парсером та же `Unterminated string`.
- Experiment: **E6** — qwen3.6-27b-fp8 + hermes parser.
- If TRUE: фикс — правка docker-compose в kurpatov-wiki-compiler.
- If FALSE: парсер ни при чём.

### H5 — universal failure of dense 24-49B class

> «Все плотные dense-модели в диапазоне 24-49B параметров падают на этой
> задаче — у них не хватает coherence/обратной связи писать JSON args
> с 40K-байтным Cyrillic file_text.»

- Predict: ни одна из {Qwen3.6-27B-FP8, Qwen3.5-27B-FP8, Qwen3-32B-FP8,
  Devstral-Small-2-24B, Mistral-Small-3.2-24B, Nemotron-Super-49B-v1.5}
  не доходит до commit source 000 при текущем skill'е.
- Falsifier: хотя бы одна из них завершает Pass-условие (см. §1).
- Experiment: батарея **E2..E7**.
- If TRUE: open-weight в этом классе требуют другого skill'а (см. H6).
- If FALSE: победитель идёт в продакшн как cheap inference baseline.

### H6 — workflow antipattern

> «Skill написан под high-coherence frontier-модели (Opus). Заставлять модель
> возвращать длинный article body внутри tool_call.arguments — антипаттерн:
> любая open-weight модель в 20-70B классе сломается на этом, не из-за нехватки
> "ума", а из-за неустойчивости JSON-сериализации длинных строк. Если skill
> декомпозировать на инкрементальные операции (terminal `cat <<EOF`, либо
> `file_editor.create` с пустым body + последовательность `str_replace_editor`
> по 1-2 секции за вызов), та же 27B модель проходит.»

- Predict: qwen3.6-27b-fp8 + декомпозированный skill (см. §5) проходит Pass-условие.
- Falsifier: та же модель падает на каком-то шаге даже при декомпозиции
  (либо новый класс ошибок: расхождение TL;DR vs body, рассыпавшийся frontmatter,
  пропущенный концепт и т.п.).
- Experiment: **E8** — qwen3.6-27b-fp8 + skill v2 (incremental write).
- If TRUE: shipping fix — переписываем `kurpatov-wiki-wiki/skills/benchmark/SKILL.md`
  и authoring.md, перезапускаем батарею.
- If FALSE: модель действительно слабая для задачи; либо нужно идти выше по размеру.

### H7 — 70B class handles current skill as-is

> «Модель уровня Llama-3.3-70B справляется с monolithic file_editor.create
> без декомпозиции skill'а — у неё хватает coherence для длинного JSON.»

- Predict: llama-3.3-70b-nvfp4 + текущий skill завершает source 000.
- Falsifier: 70B падает на том же шаге.
- Experiment: **E7** — llama-3.3-70b-nvfp4, skill v1.
- If TRUE: 70B+ — это пороговый класс «работает out of the box»; знаем,
  где провести черту между «надо переделывать skill» и «надо платить за
  размер».
- If FALSE: проблема в skill'е, не в размере.

### H8 — context starvation near 65K

> «Полный transcript ~50KB + skill ~10KB + prompts ~5KB + конкатенация
> в process истории 65K — модель теряет coherence ближе к концу контекста
> и срывается на JSON.»

- Predict: qwen3.6-27b-fp8 + усечённый transcript (первые 30KB / 50% segments)
  проходит дальше шага «write source 000».
- Falsifier: на trimmed transcript та же ошибка.
- Experiment: **E9** — qwen3.6-27b-fp8 + transcript_trim=30K.
- If TRUE: фикс на стороне skill'а (ablate transcript / chunked summarization).
- If FALSE: контекст ни при чём.

## 4. Experiment matrix

Стратегия: one-factor-at-a-time от baseline E2 (Qwen3.6-27B-FP8 monolithic).
Полный факторный дизайн = 7 моделей × 2 workflow × 2 max_tok × 3 parser ×
2 trim = 168 ячеек, неподъёмно. Поэтому: пройдём срез по моделям при
фиксированном skill v1, решим, нужна ли Phase B.

| ID  | Модель                       | Skill | max_tok | parser     | transcript | H        |
| --- | ---------------------------- | ----- | ------- | ---------- | ---------- | -------- |
| E0  | Opus 4.6 (baseline)          | v1    | default | n/a (api)  | full       | reference |
| E1  | qwen3.6-27b-awq-int4         | v1    | default | qwen3_xml  | full       | H1 ✗     |
| E2  | qwen3.6-27b-fp8 (✓ executed) | v1    | default | qwen3_xml  | full       | H1 ✗     |
| E3  | qwen3-32b-fp8                | v1    | default | qwen3_xml  | full       | H2       |
| E4  | qwen3.5-27b-fp8              | v1    | default | qwen3_xml  | full       | H2       |
| E5  | qwen3.6-27b-fp8              | v1    | 32768   | qwen3_xml  | full       | H3       |
| E6  | qwen3.6-27b-fp8              | v1    | default | hermes     | full       | H4       |
| E7  | devstral-small-2-24b         | v1    | default | hermes     | full       | H5       |
| E8  | mistral-small-3.2-24b        | v1    | default | mistral    | full       | H5       |
| E9  | nemotron-super-49b-v1.5-fp8  | v1    | default | hermes     | full       | H5       |
| E10 | llama-3.3-70b-nvfp4          | v1    | default | llama3_json| full       | H7       |
| E11 | qwen3.6-27b-fp8              | **v2**| default | qwen3_xml  | full       | H6       |
| E12 | qwen3.6-27b-fp8              | v1    | default | qwen3_xml  | trim 30K   | H8       |
| E13 | (winner of E3..E10)          | v2    | default | --         | full       | confirm H6|

Cheap-first ordering: E5 (1 cycle, никаких новых моделей) → E6 (тот же
вес, swap parser) → E12 (тот же вес, trim transcript) → E3/E4 (re-use
weights cache for Qwen3-family) → E7/E8 → E9 → E10. Затем, если ничто
не прошло — Phase B: E11 + E13.

## 5. Skill v2 design (conditional, для E11)

Включаем, только если E2..E10 в массе провалились на одинаковом
шаге `file_editor.create source.md`. Идея — заменить monolithic write на
поток мелких операций, в каждой из которых JSON args ≤ 4 KB:

1. **Stub-create**: `file_editor.create` с минимальным body — только
   frontmatter (`---\n...\n---\n# {title}\n\n## TL;DR\n\nstub\n`).
2. **Section-by-section append**: для каждой из секций
   (`TL;DR`, `Claims`, `New ideas`, `All ideas`, `Notes`)
   отдельный вызов `file_editor.str_replace` или `insert`,
   c body ≤ 200 строк / ≤ 8 KB.
3. **Concept files**: на каждый концепт — отдельный `file_editor.create`
   с маленьким файлом (~20 строк, ~1 KB).
4. **Index update**: `file_editor.str_replace` точечный — добавить
   строку/объект, не переписывать концепт-индекс целиком.
5. **Commit**: terminal `git add -A && git commit -m '...' && git push`.

Контракт: «никогда не передавай в JSON tool args строку длиннее 8 KB».
Это явное правило в skill v2 + добавим автотест на агентский цикл,
который ловит size-overflow до отправки.

## 6. Decision flowchart

```
Run E5/E6/E12 (cheap reconfigs of qwen3.6-27b-fp8)
    │
    ├── any pass → DONE for H3/H4/H8; cascade fix to compose/.env, re-run battery
    │
    └── all fail
            │
            └── Run E3/E4/E7/E8/E9 (other 24-49B models, skill v1)
                    │
                    ├── any pass → log winner, treat as "skill v1-compatible"; H5 refuted
                    │
                    └── all fail (H5 strongly supported)
                            │
                            └── Run E10 (llama-70b, skill v1)
                                    │
                                    ├── pass → H7 confirmed (size threshold);
                                    │           ship 70B as default for prod-grade,
                                    │           still build skill v2 for cost
                                    │
                                    └── fail → Phase B (skill v2)
                                            │
                                            └── Run E11 (qwen3.6-27b-fp8 + skill v2)
                                                    │
                                                    ├── pass → ship skill v2,
                                                    │           re-run E3..E9 on v2
                                                    │
                                                    └── fail → 27B класс
                                                              нерешает задачу
                                                              даже декомпозированно;
                                                              recommend dual-GPU TP
                                                              для 123B+
```

## 7. Что НЕ делаем

- Не пытаемся «уговаривать» модель prompt-инжинирингом писать короче
  внутри одного file_editor.create — это та же ставка, что monolithic
  workflow, просто слабее.
- Не отключаем `enable_thinking` ради экономии токенов — у Qwen3.6
  думающие токены и так выключены через `chat-template-kwargs`; снимать
  больше нечего.
- Не trade'им качество на проходимость (например, «пиши только TL;DR,
  пропусти Claims» — это меняет definition of pass и обесценивает
  сравнение с Opus baseline).

## 8. Open questions

- В каком формате логировать «пройдено / не пройдено» для каждой
  ячейки матрицы — отдельный JSON в `experiments/<run>/verdict.json`,
  ли скрипт `check-pass.sh`? Решение нужно до E3.
- Имеет ли смысл ablate `concepts_introduced` шаг (т.е. бенчить только
  source-статью, без концептов) — это меньше работы, более узкий
  тест на JSON-truncation, но другое определение pass.
- Когда добавлять Devstral-2-123B и dense >70B — сейчас они в `skip:true`,
  потому что требуют dual-GPU TP. Вынести отдельной фазой после H7.

## 9. История ревизий

| ver  | дата       | что изменилось                                |
| ---- | ---------- | --------------------------------------------- |
| 0.1  | 2026-04-25 | initial draft после E2 (qwen3.6-27b-fp8 fail) |
