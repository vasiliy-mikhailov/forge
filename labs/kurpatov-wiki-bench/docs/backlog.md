# Research Backlog — kurpatov-wiki-compiler

Сырой список всех гипотез. Подход и общая методология — в [`spec.md`](spec.md).
Детальный спек активной гипотезы — в `experiments/<id>.md`, ссылка
проставлена в колонке `Spec`. Правило: детальный спек пишется только
для тех гипотез, что запускаем в ближайшие 48 часов. Всё остальное
живёт здесь как одна строка-триаж.

## Scoring (ICE)

`ICE = I × C × E`, диапазон 1–1000. По 1–10 баллов:

- **I (Impact)** — насколько приближает к Target Condition (см. spec.md §1).
- **C (Confidence)** — насколько уверены, что сработает (статьи, прецеденты,
  наша интуиция). Низкий C ≠ плохо: «низкая confidence + высокий impact +
  лёгкая проверка» — типовой профиль рискованной ставки.
- **E (Ease)** — 1 = недели работы; 10 = минуты конфига.

Берём top-3 по ICE как кандидатов на следующий `spec.md`.

## Lifecycle

`backlog → triaged → spec → running → done | refuted | skip`

- **backlog** — записано, не оценено или оценено низко.
- **triaged** — оценили, в топе, ждёт написания spec.
- **spec** — spec.md написан, готов к запуску.
- **running** — эксперимент идёт.
- **done** — завершён, результат в Post-Mortem spec'а.
- **refuted** — фальсифицирован.
- **skip** — технически невозможно (модели нет на HF, нет железа и т.п.).

## A. Inference config tweaks (cheapest, top of stack)

| ID  | Идея                                                                              |  I |  C |  E |  ICE | Status | Spec |
| --- | --------------------------------------------------------------------------------- | -: | -: | -: | ---: | ------ | ---- |
| A1  | bump `max_completion_tokens` до 32 768 для open-weight runs                       |  6 |  2 | 10 |  120 | backlog | — |
| A2  | swap parser `qwen3_xml` → `hermes` на Qwen3.6-27B-FP8                              |  6 |  3 | 10 |  180 | backlog | — |
| A3  | enforce `tool_choice="required"` (vs auto) — снимает ambiguity                     |  4 |  4 | 10 |  160 | backlog | — |
| A4  | **vLLM guided JSON decoding** (xgrammar / outlines) — schema-enforced tool args   |  8 |  7 |  6 |  336 | triaged | — |
| A5  | `lm-format-enforcer` поверх vLLM — внешний грамматический enforcer                 |  7 |  6 |  5 |  210 | backlog | — |
| A6  | KV cache `int8` вместо `fp8` — больше эффективного контекста                       |  2 |  5 |  8 |   80 | backlog | — |
| A7  | enable `--enable-prefix-caching` подтверждённо (уже on?) — speedup длинных промптов|  2 |  6 |  9 |  108 | backlog | — |

## B. Different models, same skill v1 (до H6 — пробуем «купить» проход размером)

| ID  | Идея                                                                              |  I |  C |  E |  ICE | Status | Spec |
| --- | --------------------------------------------------------------------------------- | -: | -: | -: | ---: | ------ | ---- |
| B1  | Qwen3.5-27B-FP8 на T1 microbench (предыдущее семейство, тот же класс)             |  4 |  5 |  8 |  160 | backlog | — |
| B2  | Qwen3-32B-FP8 на T1 (старее, должна быть стабильнее)                               |  4 |  5 |  8 |  160 | backlog | — |
| B3  | gpt-oss-20b (веса уже в кэше, dense bf16)                                          |  4 |  5 | 10 |  200 | backlog | — |
| B4  | Devstral-Small-2-24B на T1                                                        |  4 |  5 |  8 |  160 | backlog | — |
| B5  | Mistral-Small-3.2-24B на T1                                                       |  4 |  4 |  8 |  128 | backlog | — |
| B6  | Nemotron-Super-49B-v1.5-fp8 на T1                                                  |  5 |  5 |  6 |  150 | backlog | — |
| B7  | Llama-3.3-70B-NVFP4 на T1+T3                                                      |  5 |  5 |  4 |  100 | backlog | — |
| B8  | Phi-4 14B (small, fast baseline; покажет линейную зависимость от размера)         |  3 |  4 | 10 |  120 | backlog | — |
| B9  | Llama-3.1-70B (older) — чтобы понять, регрессия ли в Llama-3.3                     |  4 |  4 |  4 |   64 | backlog | — |
| B10 | Mistral-Large-2 123B FP8 (если существует на HF)                                  |  6 |  6 |  2 |   72 | backlog | — |

## C. Different inference engine

| ID  | Идея                                                                              |  I |  C |  E |  ICE | Status | Spec |
| --- | --------------------------------------------------------------------------------- | -: | -: | -: | ---: | ------ | ---- |
| C1  | ollama swap — другой tokenizer pipeline, может укладывать длинный JSON корректно   |  3 |  3 |  6 |   54 | backlog | — |
| C2  | llama.cpp GGUF Q5_K_M — другая кодировка весов, другой decode-loop                 |  3 |  3 |  5 |   45 | backlog | — |
| C3  | TensorRT-LLM compiled engine — другой path, может править FP8 corner cases         |  3 |  4 |  3 |   36 | backlog | — |
| C4  | SGLang — другой engine, явно ориентирован на structured outputs                    |  4 |  5 |  4 |   80 | backlog | — |
| C5  | vLLM **>** v0.19 (latest) — апстрим могли пофиксить tool parser                    |  3 |  4 |  9 |  108 | backlog | — |

## D. Skill / workflow design (THE BET cluster)

| ID  | Идея                                                                              |  I |  C |  E |  ICE | Status | Spec |
| --- | --------------------------------------------------------------------------------- | -: | -: | -: | ---: | ------ | ---- |
| D1  | **skill v2** — incremental: stub-create + section-by-section str_replace ≤ 4 KB  | 10 |  7 |  3 |  210 | backlog | — |
| D2  | skill v3 — terminal-only writes: `cat > file <<'EOF'` heredoc, без file_editor    |  8 |  8 |  4 |  256 | triaged | — |
| D3  | skill v4 — local write через terminal + atomic git commit/push в одном bash       |  7 |  8 |  4 |  224 | triaged | — |
| D4  | skill v5 — двухфазный: «черновик целиком (короткий)» → «детализация по секциям»   |  4 |  3 |  3 |   36 | backlog | — |
| D5  | skill v6 — 1 agent run = 1 секция (TL;DR run, Claims run, Notes run)               |  5 |  6 |  3 |   90 | backlog | — |
| D6  | skill: pre-flight check, убирающий `summary` из tool-call (можем экономить токены) |  2 |  3 |  9 |   54 | backlog | — |

## E. Data preprocessing

| ID  | Идея                                                                              |  I |  C |  E |  ICE | Status | Spec |
| --- | --------------------------------------------------------------------------------- | -: | -: | -: | ---: | ------ | ---- |
| E1  | trim transcript source 000 до 30 KB (первые 1000 из 1614 сегментов)               |  4 |  2 |  9 |   72 | backlog | — |
| E2  | глобальный trim для всех source 005 модуля                                         |  2 |  4 | 10 |   80 | backlog | — |
| E3  | pre-summarize transcript отдельным LLM-step'ом до агентского цикла                 |  4 |  5 |  6 |  120 | backlog | — |
| E4  | chunked summarization (10K tokens chunks) → агенту приходит уже компактный текст  |  5 |  4 |  4 |   80 | backlog | — |
| E5  | drop whisper segments, передавать только plain text (без timestamps)               |  2 |  4 | 10 |   80 | backlog | — |

## F. Eval / metrics (instrumentation)

| ID  | Идея                                                                              |  I |  C |  E |  ICE | Status | Spec |
| --- | --------------------------------------------------------------------------------- | -: | -: | -: | ---: | ------ | ---- |
| F1  | **T1 microbench L*** — численный порог JSON-tool-args на синтетических Cyrillic   |  8 |  9 |  9 |  **648** | **spec** | [experiments/F1.md](experiments/F1.md) |
| F2  | self-loop quality grader (агент оценивает свой output по rubric)                   |  6 |  5 |  4 |  120 | backlog | — |
| F3  | cross-model voting (≥3 модели на одном source, мажоритарно)                        |  4 |  4 |  3 |   48 | backlog | — |
| F4  | GPT-4o pairwise judge (Opus-output vs open-weight-output, blind)                   |  6 |  7 |  5 |  210 | backlog | — |
| F5  | claim-level fact-check coverage metric (per source)                                |  4 |  5 |  4 |   80 | backlog | — |

## G. Infrastructure

| ID  | Идея                                                                              |  I |  C |  E |  ICE | Status | Spec |
| --- | --------------------------------------------------------------------------------- | -: | -: | -: | ---: | ------ | ---- |
| G1  | dual-GPU TP=2 (Blackwell + 5090) — 70B–123B без квантования                        |  6 |  8 |  2 |   96 | backlog | — |
| G2  | speculative decoding с draft-model (Qwen3-1.7B) — ускорить batch                   |  5 |  5 |  3 |   75 | backlog | — |
| G3  | warm-pool of containers — убрать 5–10 мин compose-up из каждого цикла              |  3 |  6 |  4 |   72 | backlog | — |

## Refuted / skipped

| ID  | Идея                                          | Причина                                                                                          |
| --- | --------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| H1  | community AWQ-INT4 виноват                    | refuted 2026-04-25: official FP8 падает идентично                                                |
| —   | gpt-oss-120b как dense baseline               | skip: gpt-oss-120b — это MoE, не dense; уже есть в кэше но не подходит под H5                    |
| —   | Qwen3.6-82B / Nemotron-5 125B                 | skip: не существуют на HF (проверено через API)                                                  |

## Top-10 by ICE (current ranking)

1. **F1 (H0) — T1 microbench L\*** = 648 ← active spec
2. A4 — vLLM guided JSON decoding = 336
3. D2 — skill v3 terminal-only = 256
4. D3 — skill v4 local-write + git terminal = 224
5. F4 — GPT-4o pairwise judge = 210
6. D1 — skill v2 incremental sections = 210
7. A5 — lm-format-enforcer = 210
8. B3 — gpt-oss-20b on T1 = 200
9. A2 — hermes parser swap = 180
10. A3 — tool_choice required = 160

После закрытия F1 (H0) пересматриваем оценки в свете полученного `L*`.
В частности:

- если `L*` ≥ 32 KB на дефолте — A1 (max_tok bump) теряет смысл (Conf → 1).
- если `L*` ≤ 4 KB — D1/D2/D3 поднимают Confidence до 9 (тогда сериализационная природа бага доказана).
- если разные модели имеют принципиально разный `L*` — B-cluster становится приоритетнее.

## Conventions

- ID идеи стабильный: A1, B3 и т.д. Гипотеза при «pivot»'е получает
  новый ID (не переписываем старый).
- Спек в колонке `Spec` ссылается на отдельный файл, обычно
  `experiments/exp_<ID>_<short>/spec.md`. Главный активный — корневой
  `spec.md`.
- ICE пересчитываем после каждой записи в Post-Mortem действующего spec'а
  (см. spec.md §6). Раз в неделю — full triage всего бэклога.
