# Research Backlog — kurpatov-wiki-compiler

Список всех гипотез по улучшению skill+harness'а (см. [`spec.md` §1](spec.md)).
Каждая гипотеза — попытка либо переписать сам skill (D, **the bet**),
либо снять необходимость его переписывать через дешёвые правки модели,
конфига или инфраструктуры (A/B/C/E/G), либо построить инструментацию
для сравнения (F).

Детальный спек активной гипотезы — в `experiments/<id>.md`, ссылка
проставлена в строке. Правило: детальный спек пишется только для тех,
что запускаем в ближайшие 48 часов.

ICE-формула, lifecycle, категории — в [`spec.md`](spec.md) §3, §8.

## Top-10 by ICE (текущий ranking)

| # | ID  | title                                       | ICE | status   | spec                                  |
|---| --- | ------------------------------------------- | ---:| -------- | ------------------------------------- |
| 1 | F1  | microbench `L*` (instrumentation)           | 648 | **spec** | [experiments/F1.md](experiments/F1.md)|
| 2 | A4  | vLLM guided JSON decoding                   | 336 | backlog  | —                                     |
| 3 | D2  | skill v3 — terminal-only writes             | 256 | triaged  | —                                     |
| 4 | D3  | skill v4 — local write + git terminal       | 224 | triaged  | —                                     |
| 5 | F4  | GPT-4o pairwise judge                       | 210 | backlog  | —                                     |
| 6 | D1  | skill v2 — incremental sections             | 210 | backlog  | —                                     |
| 7 | A5  | lm-format-enforcer                          | 210 | backlog  | —                                     |
| 8 | B3  | gpt-oss-20b на T1                           | 200 | backlog  | —                                     |
| 9 | A2  | hermes parser swap                          | 180 | backlog  | —                                     |
|10 | A3  | tool_choice="required"                      | 160 | backlog  | —                                     |

## A. Inference config tweaks

Дешёвые правки vLLM-флагов или OpenHands LLMConfig. Не трогают модель и не
трогают skill — проверяем «не выстрелит ли при правильной настройке».

#### A1 — bump `max_completion_tokens` до 32 768

**ICE 120 (6 · 2 · 10) · backlog**

В OpenHands LLMConfig (передаётся через `bench/run.sh`) поднять
`max_completion_tokens` с дефолта (~4096) до 32 768. Сработает, если
модель не успевает дописать 40 KB JSON-args до того, как vLLM срубит
ответ — увидим `stop_reason=length` и усечённый JSON. Bump покрывает
40 KB Cyrillic body (~16K токенов).
*Опровергнуто, если в логах run'а `stop_reason ≠ length` (модель сама
закончила раньше), либо при max=32K тот же `Unterminated string`.*

#### A2 — swap parser `qwen3_xml` → `hermes`

**ICE 180 (6 · 3 · 10) · backlog**

В `labs/kurpatov-wiki-compiler/docker-compose.yml` — флаг
`--tool-call-parser` с `qwen3_xml` на `hermes`. `qwen3_xml` — относительно
свежий парсер, может неправильно обрамлять Cyrillic в XML-обёртке;
`hermes` — старее и обкатан.
*Опровергнуто, если при hermes тот же `Unterminated string` (баг не в
парсере), либо TPS падает > 30% (TPS guardrail).*

#### A3 — `tool_choice="required"`

**ICE 160 (4 · 4 · 10) · backlog**

В OpenHands LLMConfig — `tool_choice` с `auto` на `required`. Заставляет
модель всегда выбирать tool, не уходить в free-text. Иногда модель
выдаёт mixed content (free-text + tool call), и парсер захлёбывается;
`required` форсит чистый tool-call вывод.
*Опровергнуто, если тот же `Unterminated string`, либо модель зацикливается
на одних и тех же tool calls.*

#### A4 — vLLM **guided JSON decoding**

**ICE 336 (8 · 7 · 6) · backlog**

В compose `--guided-decoding-backend xgrammar` (или outlines).
В OpenHands sampling params — JSON schema для tool args через
`response_format` / `guided_json`. Guided decoding принудительно держит
выход в рамках schema: модель **не может** закрыть строку без `"`,
не может оборвать args. JSON-truncation технически невозможна.
*Опровергнуто, если TPS падает > 50% (overhead), либо модель «зависает»
в loop'е, не способная завершить генерацию валидного JSON.*

#### A5 — `lm-format-enforcer`

**ICE 210 (7 · 6 · 5) · backlog**

Альтернатива A4: добавить grammar enforcer на стороне sampler'а
(не engine'а), интегрировать в OpenHands. Может быть совместимо с
большим числом моделей чем xgrammar.
*Опровергнуто, если интеграция нетривиальна (Cost вырастает до 3 →
пересчитать ICE), либо crash повторяется на тестовом прогоне.*

#### A6 — KV cache `int8` вместо `fp8`

**ICE 80 (2 · 5 · 8) · backlog**

`--kv-cache-dtype int8` в compose. Освобождает VRAM, может позволить
больший max_model_len или batch. Маловероятно чинит JSON-truncation,
но дёшево попробовать; может убрать `WARNING uncalibrated q_scale 1.0`
из логов FP8-attention.
*Опровергнуто, если quality drops > 20% (skill quality regression
guardrail), либо тот же crash.*

#### A7 — подтвердить `--enable-prefix-caching`

**ICE 108 (2 · 6 · 9) · backlog**

По логам v0.19 prefix caching включён по умолчанию. Подтвердить и
включить если нет. Повторные turn'ы агента (один и тот же skill-prefix)
кэшируются → модель тратит attention budget только на свежий контекст.
*Опровергнуто, если prefix caching не влияет на observable behavior
(TPS не растёт, crash остаётся).*

## B. Different models, same skill v1

«Купить» проход размером модели или сменой семейства, не трогая skill.

#### B1 — Qwen3.5-27B-FP8 на T1

**ICE 160 (4 · 5 · 8) · backlog**

В `models.yml` — `Qwen/Qwen3.5-27B-FP8`. Предыдущее поколение Qwen,
тот же класс размера. Если `L*(3.5)` ≫ `L*(3.6)` — корень в семействе 3.6.
*Опровергнуто, если `L*` отличается < 20% — баг не семейный.*

#### B2 — Qwen3-32B-FP8 на T1

**ICE 160 (4 · 5 · 8) · backlog**

`Qwen/Qwen3-32B-FP8`. Ещё на поколение раньше Qwen3.6, на 5B больше.
Если `L*` существенно выше — двойное подтверждение Qwen3.6-специфики.
*Опровергнуто, если `L*` ≈ Qwen3.6 — общая слабость dense-30B класса.*

#### B3 — gpt-oss-20b на T1

**ICE 200 (4 · 5 · 10) · backlog**

`unsloth/gpt-oss-20b` — веса уже в кэше (`${STORAGE_ROOT}/shared/models/`,
~13 GB). Совершенно другая архитектура (OpenAI), другой instruct-tuning,
другая JSON-mode тренировка. Если `L*` > 24 KB — у нас уже есть рабочий
cheap candidate.
*Опровергнуто, если `L*` ≤ 4 KB — баг общий для open-weight 20-30B.*

#### B4 — Devstral-Small-2-24B

**ICE 160 (4 · 5 · 8) · backlog**

`mistralai/Devstral-Small-2-24B`. Code-focused tuning обычно даёт
лучшую JSON-стабильность. Mistral-семейство, hermes-style tool format.
*Опровергнуто, если `L*` ≤ Qwen3.6.*

#### B5 — Mistral-Small-3.2-24B

**ICE 128 (4 · 4 · 8) · backlog**

`mistralai/Mistral-Small-3.2-24B-Instruct`. General-purpose, не code-focused.
Mistral исторически стабильнее на JSON-tool calls чем Qwen.
*Опровергнуто, если `L*` ≈ Qwen3.6.*

#### B6 — Nemotron-Super-49B-v1.5-FP8

**ICE 150 (5 · 5 · 6) · backlog**

`nvidia/Llama-3.3-Nemotron-Super-49B-v1.5-FP8`. Большая dense (49B),
NVidia-tuned. Дальше от 24-32B размерного бутылочного горлышка.
*Опровергнуто, если `L*` < 8 KB на синтетике или crash на T3.*

#### B7 — Llama-3.3-70B-NVFP4

**ICE 100 (5 · 5 · 4) · backlog**

`nvidia/Llama-3.3-70B-Instruct-FP4`. ~50 GB на одной Blackwell.
Большой dense, классический «70B threshold» candidate. Если она
проходит skill v1 без правок — мы платим железом, избегаем правки skill'а.
*Опровергнуто, если на T1 `L*` ≈ Qwen3.6, или на T3 тот же crash —
тогда 70B недостаточно для skill v1.*

#### B8 — Phi-4 14B

**ICE 120 (3 · 4 · 10) · backlog**

`microsoft/phi-4`. Маленькая, быстрая, натренена под JSON и tool use.
Если неожиданно вытянет — отличный cheap baseline.
*Опровергнуто, если `L*` ≤ 4 KB.*

#### B9 — Llama-3.1-70B (older)

**ICE 64 (4 · 4 · 4) · backlog**

`meta-llama/Llama-3.1-70B-Instruct`. Проверка regression: может ли быть
3.3 хуже 3.1 на JSON. Skip-able, если B7 сразу проходит.
*Опровергнуто, если `L*` примерно равны — поколение не влияет.*

#### B10 — Mistral-Large-2 123B FP8

**ICE 72 (6 · 6 · 2) · backlog · depends on G1**

`mistralai/Mistral-Large-Instruct-2411-FP8` (если на HF). Требует TP=2
(Blackwell+5090). Топовый dense размер. Финальный «может ли вообще
open-weight skill v1». Зависит от G1 (dual-GPU TP).
*Опровергнуто, если G1 fail; либо `L*` всё равно ≤ Qwen3.6.*

## C. Different inference engine

Сменить движок, оставив модель и skill. Проверяем «не баг ли это vLLM».

#### C1 — ollama swap

**ICE 54 (3 · 3 · 6) · backlog**

Поднять ollama (cuda backend), тот же модельный вес. Другой decode loop,
другой tokenizer pipeline. Если crash — артефакт vLLM-streaming, ollama
может не воспроизвести.
*Опровергнуто, если тот же `Unterminated string` или TPS заметно ниже.*

#### C2 — llama.cpp GGUF Q5_K_M

**ICE 45 (3 · 3 · 5) · backlog**

`llama-server` (llama.cpp) с GGUF Q5_K_M. Полностью другой engine, другой
sampler. Если crash — артефакт shared-tensor compute path в vLLM,
llama.cpp его не разделяет.
*Опровергнуто, если тот же crash; quality drop из-за квантования.*

#### C3 — TensorRT-LLM compiled engine

**ICE 36 (3 · 4 · 3) · backlog**

Скомпилировать модель в TRT engine, запускать через trtllm-serve. Другой
path сериализации, другие FP8 ядра. Может править corner-case bugs FP8
attention из warnings vLLM.
*Опровергнуто, если компиляция падает / crash остаётся.*

#### C4 — SGLang

**ICE 80 (4 · 5 · 4) · backlog**

SGLang server вместо vLLM. Заточен под structured outputs и tool use из
коробки; `regex` / `json_schema` constraints могли быть лучше реализованы
чем vLLM xgrammar (overlap с A4).
*Опровергнуто, если те же crash patterns; миграция требует переписывания
harness'а.*

#### C5 — vLLM upgrade (latest > v0.19)

**ICE 108 (3 · 4 · 9) · backlog**

`vllm/vllm-openai:latest` вместо `v0.19.1-cu130-ubuntu2404`. Один pull +
compose restart. Апстрим мог пофиксить qwen3_xml парсер или JSON tool
args.
*Опровергнуто, если latest не запускается на Blackwell или CUDA 13;
либо тот же crash.*

## D. Skill / workflow design (THE BET)

**Главная категория** — переписываем сам `kurpatov-wiki-wiki/skills/benchmark/SKILL.md`.
Финальный deliverable лаборатории.

#### D1 — skill v2: incremental sections

**ICE 210 (10 · 7 · 3) · backlog**

Заменить monolithic `file_editor.create source.md` (40 KB args) на
последовательность мелких операций:
1. `file_editor.create` со stub (frontmatter + пустые секции, ≤ 2 KB)
2. Per-section `file_editor.str_replace` ≤ 4 KB args
3. Concept files как отдельные мелкие `create`'ы (~1 KB каждый)
4. `concept-index.json` точечный `str_replace`, не переписываем целиком

Все JSON tool args ≤ 4 KB → ниже observed threshold. THE BET — если
работает, шипуем как `skill v2`.
*Опровергнуто, если на T2 (smoke source) тот же `Unterminated string`
на каком-то str_replace, либо модель «забывает» что уже написала
(coherence loss between sections).*

#### D2 — skill v3: terminal-only writes

**ICE 256 (8 · 8 · 4) · triaged**

Вместо `file_editor` использовать `terminal` tool с heredoc:
```
cat > /workspace/wiki/data/sources/<path>/source.md <<'EOF'
{full markdown body}
EOF
```
Body передаётся внутри bash-команды, **не** внутри JSON tool args.
Bash heredoc не страдает от JSON-escape проблем — Cyrillic, многострочность,
markdown-кавычки, всё OK. Если модель освоит этот pattern — это самое
радикальное решение.
*Опровергнуто, если модель путается с heredoc-разделителями (закрывает
не там), либо OpenHands terminal tool ограничивает длину command'а на
стороне sandbox.*

#### D3 — skill v4: local write через terminal + git одной командой

**ICE 224 (7 · 8 · 4) · triaged**

Гибрид D1+D2: контент строится инкрементально через `cat >>` (D2-style),
затем `git add -A && commit -m '...' && push origin <branch>` одной
terminal-командой. Разделяем «контентный» и «git»-этапы; контент
наращивается без JSON-tool-args.
*Опровергнуто, если не даёт прироста против D2, либо git operations
падают в сэндбоксе при большом объёме.*

#### D4 — skill v5: двухфазный «черновик → детализация»

**ICE 36 (4 · 3 · 3) · backlog**

Первый agent run пишет короткий black-bone source (TL;DR + headings, без
claims). Второй run детализирует. Две раздельные сессии, без context
handoff.
*Опровергнуто, если quality суммарного output ниже Opus baseline,
либо координация дороже выгоды.*

#### D5 — skill v6: 1 run = 1 секция

**ICE 90 (5 · 6 · 3) · backlog**

Каждая секция (TL;DR, Claims, New ideas, All ideas, Notes) — отдельный
agent run с минимальным skill-frontmatter'ом. Per-run JSON-args
тривиальны; usage модели N×.
*Опровергнуто, если total cost > Opus, либо provenance markers рассыпаются
между секциями.*

#### D6 — pre-flight тримминг `summary` поля в tool calls

**ICE 54 (2 · 3 · 9) · backlog**

В OpenHands шаблоне tool-call'а — снять обязательное `summary`. Каждый
turn шлёт `summary` ~200-500 байт; на 26 turn'ах накапливается ~10 KB
лишнего JSON.
*Опровергнуто, если поле не убрать без правки OpenHands SDK; либо `L*`
не реагирует на размер summary.*

## E. Data preprocessing

Уменьшить размер input до того, как агент его увидит. Дёшево, не трогает
skill, не трогает модель.

#### E1 — trim transcript source 000 до 30 KB

**ICE 72 (4 · 2 · 9) · backlog**

В `run.sh` env-флаг `TRANSCRIPT_TRIM_BYTES=30720`; bench-контейнер режет
`raw.json` до первых 30 KB. Меньше input → косвенно меньше output (агент
короче пишет).
*Опровергнуто, если crash на той же позиции / модель всё равно генерит
40 KB.*

#### E2 — глобальный trim на этапе ingest

**ICE 80 (2 · 4 · 10) · backlog**

Все source модуля 005 усечены до 30 KB на этапе `kurpatov-wiki-ingest`.
Skill читает уже короткий raw, идемпотентно.
*Опровергнуто, если quality финального output деградирует
(`claims_count` -30%) — теряем суть лекции.*

#### E3 — pre-summarize transcript отдельным LLM-step'ом

**ICE 120 (4 · 5 · 6) · backlog**

До запуска агента — отдельный call к compiler'у суммаризует transcript
в ~10-15 KB outline; агент видит компактный текст. LLM-сжатие сохраняет
суть лучше, чем blind trim.
*Опровергнуто, если pre-summarizer теряет важные claims (claim coverage
drop), либо сам падает на Cyrillic JSON tool args.*

#### E4 — chunked summarization

**ICE 80 (4 · 4 · 4) · backlog**

Транскрипт разбит на chunks по 10K токенов; каждый суммаризуется отдельно;
агенту приходит склеенный summary. Устойчиво при очень длинных source.
*Опровергнуто, если chunks ломают coherence claim provenance, либо
boundaries создают дубли claims.*

#### E5 — drop whisper segments, plaintext only

**ICE 80 (2 · 4 · 10) · backlog**

При формировании input агенту — выкидываем `segments[]` массив с
timestamps, оставляем плоский текст. Timestamps занимают ~30% размера
raw.json и редко используются skill'ом.
*Опровергнуто, если skill использует timestamps (например, для anchor
links). Quality drops.*

## F. Eval / metrics (instrumentation)

Меряем — без этого все остальные категории сравнивать качественно, не
количественно.

#### F1 — microbench `L*` (active spec)

**ICE 648 (8 · 9 · 9) · spec — [experiments/F1.md](experiments/F1.md)**

T1 синтетический тест: 9 длин Cyrillic body × 10 trials, измеряем
порог `L*` где pass-rate ≥ 0.95. Даёт численную метрику для сравнения
**всех** последующих гипотез (A1, A4, B-cluster, D1) — за минуты, не часы.
Самая полезная instrumentation-ставка перед всем остальным.
*Опровергнуто (см. detailed spec), если variance > 30 п.п., pass-rate
не монотонна с L, или L=1KB pass-rate < 0.95.*

#### F2 — self-loop quality grader

**ICE 120 (6 · 5 · 4) · backlog**

После agent run'а — отдельный LLM-call к compiler'у оценивает output
по rubric (полнота claims, корректность frontmatter, citations).
Score попадает в `summary.json`.
*Опровергнуто, если model self-grading плохо коррелирует с human judgment
(нужен spot-check).*

#### F3 — cross-model voting

**ICE 48 (4 · 4 · 3) · backlog**

Один source прогоняется на 3+ моделях; outputs сравниваются по majority
claims. Референс качества без human-eval.
*Опровергнуто, если модели систематически совпадают на ошибках.*

#### F4 — GPT-4o pairwise judge

**ICE 210 (6 · 7 · 5) · backlog**

GPT-4o (через API) blind-сравнивает Opus baseline output vs open-weight
output по rubric, возвращает win-rate. Calibrated quality metric.
*Опровергнуто, если GPT-4o-judge сильно biased (любит свой стиль),
требует human-spot-check.*

#### F5 — claim coverage / spec compliance metric

**ICE 80 (4 · 5 · 4) · backlog**

Считаем долю claims с правильным provenance marker (NEW / REPEATED /
CONTRADICTS). Формальная метрика skill compliance, не quality.
*Опровергнуто, если метрика тривиально проходима (модели всегда NEW).*

## G. Infrastructure

#### G1 — dual-GPU TP=2 (Blackwell + 5090)

**ICE 96 (6 · 8 · 2) · backlog**

vLLM compose с `--tensor-parallel-size 2`, GPU pinning на обе карты.
Открывает дорогу к 70-130B моделям без квантования (B10).
*Опровергнуто, если 5090 не тянет TP-shard 70B (мало VRAM); или NCCL
latency между картами убивает TPS.*

#### G2 — speculative decoding с draft Qwen3-1.7B

**ICE 75 (5 · 5 · 3) · backlog**

Маленькая draft model для speculative decoding в vLLM. Ожидаемый
TPS x1.5–2.0 → быстрее цикл, больше experiment-cells в день.
*Опровергнуто, если draft не совместим, либо speedup < 30% на нашем
паттерне (агентские turn'ы короткие).*

#### G3 — warm-pool of containers

**ICE 72 (3 · 6 · 4) · backlog**

Поднимать compiler + bench image «горячими» (idle) до начала батареи,
реюзовать между моделями. Убирает ~5–10 мин compose-up на цикл.
*Опровергнуто, если vLLM не поддерживает hot model swap (известно: нет).
Тогда warm-pool работает только для bench-контейнера, не compiler.*

## Refuted / skipped

| ID  | Идея                                          | Причина                                                                            |
| --- | --------------------------------------------- | ---------------------------------------------------------------------------------- |
| H1  | community AWQ-INT4 виноват                    | refuted 2026-04-25: official FP8 (`Qwen/Qwen3.6-27B-FP8`) падает идентично         |
| —   | gpt-oss-120b как dense baseline               | skip: gpt-oss-120b — это MoE, не dense                                             |
| —   | Qwen3.6-82B / Nemotron-5 125B                 | skip: не существуют на HF (проверено через API search)                             |
