# Шаблон скрипта customer-interview — для русскоязычных сегментов

Этот файл — каноническая **схема** per-persona скрипта customer-interview для русскоязычных продуктов forge (сегодня: kurpatov-wiki; завтра: tarasov-wiki). Per-product instance скрипты живут в private repo per [ADR 0018 § 7](../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md): `<product-wiki>/metadata/customer-interview-scripts/<persona-slug>.md`.

Per [ADR 0027 § 8](../phase-preliminary/adr/0027-product-development-approach.md): язык скрипта совпадает с native language сегмента (для kurpatov-wiki — русский primary, English code-switch только где термин precise — например, evidence-base, JTBD, RCT). **Schema-labels** (`**Severity**`, `**Affected personas**` и т. п.) остаются на английском — их парсит forge-tooling. **Содержание** — на русском.

Для англоязычных сегментов будущего продукта надо создать parallel template (`customer-interview-script-template.en.md`); сегодня это не требуется.

## Когда использовать этот шаблон

- Step 1 of customer-walk cycle (per [ADR 0016](../phase-preliminary/adr/0016-wiki-customers-as-roles.md)) уже прошёл; Wiki PM имеет walk-derived ledgers + cross-tab observations + named problems.
- Wiki PM формулирует **falsifiable hypothesis** про конкретный finding и хочет проверить его **глубинным интервью** (не повторным walk'ом).
- Per persona × per product per cycle — один скрипт. Если в одном цикле проверяются несколько гипотез, нужно несколько скриптов.

## Канонические разделы скрипта

Per-persona скрипт автор-ит с этими 7 разделами в следующем порядке. Total целевая длина: 400–600 слов.

### 1. Шапка персоны

- **Файл персоны (forge)**: link на `phase-b-business-architecture/roles/customers/<persona>.md` + одна строка-резюме в стиле «<working-tag> — <one-line описание>».
- **Job to be done (Работа клиента)**: формулировка в формате *«Когда я <ситуация>, я хочу <мотивация>, чтобы <исход>».* Копируется из persona file's § Job to be done.
- **Сигнал early-adopter**: одна строка про то, почему этот сегмент desperate за решение (наибольший pain → primary целевая аудитория для текущего цикла).

### 2. Гипотеза под проверку

- **Гипотеза**: одна falsifiable формулировка про конкретный finding из walk'а или предшествующего интервью. Должна быть достаточно specific, чтобы customer-ответ мог её confirm / refute / refine.
- **Почему falsifiable**: одна строка обоснования — что именно делает customer источником истины, на которой строится этот тест.

Шаблон гипотезы (заполнить):

> **Гипотеза**: <конкретный finding> для <persona> является <severity> для <конкретного use-case>; пофиксить его разблокирует <конкретный outcome>.
> **Почему falsifiable**: <persona> прошла корпус и может в ретроспективе ранжировать, что было наиболее disabling.

### 3. Вступительные вопросы (3, открытые)

Open-ended past-tense / present-tense вопросы, без leading «would you» / «could you». Цель — surface реальный context до того, как вводить хоть какой-то product framing.

Канонический паттерн (адаптировать под персону):

1. «Расскажите про последний раз, когда <персона делала job>...»
2. «Опишите по шагам, что вы сделали первым / следующим / в конце...»
3. «Что было самое сложное / неожиданное / запоминающееся в этом?»

### 4. Probe (5–7 вопросов; Forces of Progress + targeted)

Open-ended вопросы, drilling в гипотезу. Каноническая структура — 4 «Forces of Progress» (Bob Moesta) + 2–3 targeted probes:

4. **Push** (что вытолкнуло клиента из старого паттерна): «Что заставило вас начать <поведение> в принципе?»
5. **Pull** (что притянуло к новому): «Что было самое полезное / привлекательное в <текущем решении / альтернативе>?»
6. **Anxiety** (что пугает): «Что вас пугает в <конкретный аспект гипотезы>?»
7. **Habit** (что удерживает старое): «Когда вы упираетесь в <конкретное препятствие>, что вы делаете — <вариант 1>, <вариант 2>, <вариант 3>?»
8–10. **Targeted** (per-hypothesis, 2–3 вопроса): probes, специфичные для гипотезы. Например:
   - «Из 27 candidate-ов фактических ошибок — сколько реально дисквалифицируют цитату?»
   - «Если бы у каждого имени был one-line note — насколько быстрее вы могли бы читать?»

### 5. Confirmation / refutation criteria

Один или два вопроса, разработанные для disambiguation. Интервьюер ЗАРАНЕЕ знает, какой ответ означает CONFIRMED / REFUTED / REFINED.

Шаблон (заполнить):

11. «Если бы вы могли пофиксить ОДНУ вещь в <product> — что это было бы?»
   - **Confirms hypothesis**, если персона скажет: <конкретный signal — формулировка, близкая к гипотезе>.
   - **Refutes hypothesis**, если персона скажет: <конкретный signal — другой finding>.
   - **Refines hypothesis**, если персона скажет: «<X>, И <Y>» — capture оба, prioritise первое.

12. (опционально) «А ВТОРАЯ по приоритету?» — disambiguation между finding'ами в одной cluster.

### 6. Закрытие (2 вопроса)

13. «Кто ещё / какие коллеги / какие знакомые делают то же самое и выиграли бы от этого?» (referrals signal — кто следующие interview-кандидаты)
14. «О чём я не спросил, что вы хотели бы добавить?» (open close — surface'ит что persona тоже считает важным, но что не было покрыто)

### 7. Заметки авторам (Authoring notes)

- **Voice fidelity**: persona-specific verbatim register (verbatim фразы из persona file's § Voice fingerprint). Не фильтровать; capture verbatim в transcript.
- **Anti-examples**: какие formulations НЕ задавать. Каноническое правило — никаких «would you» / «could you» / «if we built X, would you...» (future-tense aspirational; persona скажет yes из вежливости — это шум).
- **Disambiguation engine**: один вопрос (обычно Q11) — это decisive moment скрипта; если ответ persona не disambiguates гипотезу, скрипт нужно ревизить.
- **Cross-persona контаминация**: НЕ использовать voice tells других персон (Marina cite-with-year — её tell; Анна «не применимо» — её tell; Антон-PM «коротко» — его tell; Антон-designer «блин» / «СТОП» — его tell). Каждый persona в собственном регистре.

## Authoring rules (правила авторства)

- Один скрипт per persona × per product per cycle. Тот же persona для другого продукта = другой скрипт (Job statement может отличаться).
- Все вопросы open-ended (нет Yes / No). Один leading вопрос = скрипт нужно ревизить.
- Total time budget: ~30 min real interview, ~15 min simulated-persona-agent interview. Скрипт questions подобрать в этот объём.
- Скрипт — **floor, не ceiling** — protocol позволяет follow-up probes, которых в скрипте нет (per [protocol document](./customer-interview-protocol.md)).

## Cross-references

- [Customer-interview protocol](./customer-interview-protocol.md) — как **проводить** интервью (правила multi-turn dialogue, transcript schema).
- [Customer-walk cycle](./wiki-customer-walk.md) — breadth-coverage walk, который ОБЫЧНО предшествует depth-probe interviews.
- [ADR 0027 § 8](../phase-preliminary/adr/0027-product-development-approach.md) — language-primary policy.
- [ADR 0018 § 7](../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md) — privacy boundary (per-product instance скрипты живут private).

## Measurable motivation chain

Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: 5 первых customer-interview скриптов для kurpatov-wiki были авторены каждый в своём template'е — schema drift, hard-to-read, инconsistencies. Per architect call: «давай сделаем для этой активности шаблон и пусть он будет на русском полностью».
- **Goal**: [Architect-velocity](../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Один шаблон → меньше ad-hoc решений per persona; быстрее аудит conformance скриптов.
- **Outcome**: каноническая схема скрипта customer-interview с 7 секциями, polностью на русском; per-product instance скрипты переписаны под этот шаблон; будущие циклы цитируют этот шаблон.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: устраняет per-script schema drift; будущий audit walker может проверять conformance per-script к этому шаблону по структуре разделов.
- **Capability realised**: [Architecture knowledge management](../phase-b-business-architecture/capabilities/forge-level.md) — meta-capability of keeping forge's discipline consistent; этот template — meta-method, не wiki-product-specific.
- **Function**: Schema-customer-interview-script-russian-segments.
- **Element**: этот файл.
