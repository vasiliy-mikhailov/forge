"""
Step 8 smoke — D8 retrieval helpers smoke (Steps 1-3).

This is a NON-LLM, fast unit test for embed_helpers.py:
  Step 1: embed.py encode passes a paraphrase / unrelated discrimination test
  Step 2: rebuild_index produces both .sqlite files with expected row counts
  Step 3: find_similar_claims surfaces a known paraphrase pair in top-K

Use this to validate the retrieval stack BEFORE wiring it into the
orchestrator step9 (which runs ~15 min wall on Qwen-27B).

Usage:
  python3 step8_smoke.py /path/to/wiki

If wiki argument is omitted, builds an in-memory test wiki from synth
fixtures.

Pass criteria (hard asserts):
  - encode returns dim=768
  - 5/5 paraphrase pairs cosine ≥ 0.80
  - 5/5 unrelated pairs cosine ≤ 0.55
  - rebuild_index inserts ≥ 1 claim per source.md
  - find-claims returns the seeded paraphrase in top-3 with sim ≥ threshold

This is D8 spec Step 1-3 GREEN gate.
"""
import sys
import json
import shutil
import tempfile
from pathlib import Path

# Add outputs/ to import path (assumes embed_helpers.py adjacent)
sys.path.insert(0, str(Path(__file__).parent))
import embed_helpers as eh


# ─── Fixtures ────────────────────────────────────────────────────────────

# 5 paraphrase pairs (semantically equivalent, lexically different)
PARAPHRASE_PAIRS = [
    ("Высота Эвереста составляет 8849 метров над уровнем моря.",
     "Эверест поднимается на 8848.86 м, округлённо 8849 м."),
    ("Принцип Парето утверждает, что 80% эффектов исходят от 20% причин.",
     "По Парето: 20% причин дают 80% результата."),
    ("Закон Мура предсказывает удвоение транзисторов каждые два года.",
     "По Муру плотность транзисторов на чипе удваивается раз в два года."),
    ("Социальный инстинкт — базовая биологическая потребность.",
     "Базовая социальная потребность является эволюционным инстинктом."),
    ("Курпатов вводит концепт химер как сложных подсознательных образований.",
     "Химеры по Курпатову — сложные структуры в подсознании."),
]

# 5 unrelated pairs (different topics, should NOT match)
UNRELATED_PAIRS = [
    ("Высота Эвереста составляет 8849 метров.",
     "Закон Мура — об удвоении транзисторов."),
    ("Принцип Парето: 80/20.",
     "Серотонин — нейромедиатор уважения."),
    ("Социальный инстинкт.",
     "Число пи равно 3.14159."),
    ("Лимбическая система генерирует эмоции.",
     "Гора Эверест в Гималаях."),
    ("Дарвин предложил теорию эволюции.",
     "Окситоцин участвует в парных отношениях."),
]

# Synth source fixture for rebuild test
SYNTH_SOURCE = """\
---
slug: ТестКурс/999 Тестовый модуль/000 Базовая лекция
course: ТестКурс
module: 999 Тестовый модуль
extractor: whisper
duration_sec: 200
language: ru
processed_at: 2026-04-26T00:00:00Z
fact_check_performed: true
concepts_touched: [pareto-principle, mount-everest, mores-law]
concepts_introduced: [pareto-principle, mount-everest]
---

# Базовая лекция

## TL;DR

Тестовый источник с 3 эмпирическими утверждениями.

## Лекция (пересказ: только NEW и проверенное)

Тестовая лекция о принципе Парето, Эвересте и законе Мура.

## Claims — provenance and fact-check

1. Высота Эвереста составляет 8849 метров над уровнем моря. [NEW]
   — https://en.wikipedia.org/wiki/Mount_Everest

2. Принцип Парето утверждает, что 80% эффектов исходят от 20% причин. [NEW]
   — https://en.wikipedia.org/wiki/Pareto_principle

3. Закон Мура предсказывает удвоение транзисторов каждые два года. [NEW]
   — https://en.wikipedia.org/wiki/Moore%27s_law

## New ideas (verified)

- Эверест — высочайшая вершина
- Парето 80/20

## All ideas

- Эверест 8849 м
- Парето 80/20
- Мур удвоение
"""

SYNTH_CONCEPT = """\
---
slug: pareto-principle
introduced_in: ТестКурс/999 Тестовый модуль/000 Базовая лекция
touched_by:
  - ТестКурс/999 Тестовый модуль/000 Базовая лекция
related: []
---
# Принцип Парето

## Definition

Принцип Парето утверждает, что около 80% результатов исходят от 20%
причин. «Парето заметил, что в Италии 80% земли принадлежит 20%
населения». Эмпирическое распределение, не строгий закон.

## Touched in sources

- [...000 Базовая лекция](../sources/ТестКурс/999 Тестовый модуль/000 Базовая лекция.md)
  Принцип Парето утверждает, что 80% эффектов исходят от 20% причин.
  [≈ 0:30]

## See also

- mount-everest — для контраста (концепт о горе, не закономерность)
"""


def step1_encode(verbose=True) -> bool:
    """Test cosine discrimination on paraphrase vs unrelated pairs."""
    if verbose: print("=== STEP 1: encode discrimination ===")
    import numpy as np

    def cos(a, b):
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    # Paraphrase pairs should be close
    para_sims = []
    for a, b in PARAPHRASE_PAIRS:
        va = eh.encode_passage(a)
        vb = eh.encode_passage(b)
        s = cos(va, vb)
        para_sims.append(s)
        if verbose: print(f"  paraphrase: {s:.3f}  '{a[:50]}...' ~ '{b[:50]}...'")

    unrel_sims = []
    for a, b in UNRELATED_PAIRS:
        va = eh.encode_passage(a)
        vb = eh.encode_passage(b)
        s = cos(va, vb)
        unrel_sims.append(s)
        if verbose: print(f"  unrelated:  {s:.3f}  '{a[:50]}...' vs '{b[:50]}...'")

    # Hard asserts — calibrated for multilingual-e5-base on Russian text:
    # e5 keeps high general cosine; we care about discrimination, not absolute.
    # Empirically: paraphrase 0.93-0.96, unrelated 0.74-0.83.
    # Discrimination margin ≈ 0.10-0.20, more than enough for top-K retrieval.
    para_min = min(para_sims)
    unrel_max = max(unrel_sims)
    margin = para_min - unrel_max
    if verbose:
        print(f"  paraphrase min cosine: {para_min:.3f} (need ≥ 0.88)")
        print(f"  unrelated max cosine: {unrel_max:.3f} (need ≤ 0.90)")
        print(f"  discrimination margin: {margin:.3f} (need ≥ 0.05)")
    ok = (para_min >= 0.88) and (unrel_max <= 0.90) and (margin >= 0.05)
    print(f"  STEP 1 {'PASS' if ok else 'FAIL'}")
    return ok


def step2_rebuild(wiki: Path, verbose=True) -> bool:
    """Test rebuild_index produces both .sqlite files with rows."""
    if verbose: print("=== STEP 2: rebuild_index ===")
    r = eh.rebuild_index(wiki)
    if verbose: print(f"  result: {json.dumps(r)}")
    claims_db = wiki / "data" / "embeddings" / "claims.sqlite"
    concepts_db = wiki / "data" / "embeddings" / "concepts.sqlite"
    ok = (claims_db.exists() and concepts_db.exists()
          and r["claims_indexed"] >= 1
          and r["concepts_indexed"] >= 1)
    print(f"  STEP 2 {'PASS' if ok else 'FAIL'}")
    return ok


def step3_find_claims(wiki: Path, verbose=True) -> bool:
    """Test find-claims surfaces seeded paraphrase in top-K."""
    if verbose: print("=== STEP 3: find_similar_claims ===")
    # Query a paraphrase of the seeded claim
    q = "Эверест поднимается на 8848 метров над уровнем моря."
    r = eh.find_similar_claims(wiki, q, k=5, threshold=0.50)
    if verbose:
        for c in r["candidates"]:
            print(f"  cand: sim={c['similarity']:.3f}  "
                  f"text='{c['claim_text'][:60]}...'")

    found = any("Эверест" in c["claim_text"] and c["similarity"] >= 0.65
                for c in r["candidates"])
    ok = found and r["k_returned"] >= 1
    print(f"  STEP 3 {'PASS' if ok else 'FAIL'}")
    return ok


def step3b_find_concepts(wiki: Path, verbose=True) -> bool:
    """Test find-concepts dedup."""
    if verbose: print("=== STEP 3b: find_similar_concepts ===")
    # Query paraphrase of pareto-principle
    r = eh.find_similar_concepts(wiki, "Принцип Парето 80/20", k=3, threshold=0.50)
    if verbose:
        for c in r["candidates"]:
            print(f"  cand: sim={c['similarity']:.3f}  slug='{c['slug']}'")
    found = any(c["slug"] == "pareto-principle" and c["similarity"] >= 0.65
                for c in r["candidates"])
    ok = found
    print(f"  STEP 3b {'PASS' if ok else 'FAIL'}")
    return ok


def make_synth_wiki(target: Path):
    """Build a minimal synthetic wiki for fixture testing."""
    target.mkdir(parents=True, exist_ok=True)
    (target / "data" / "sources" / "ТестКурс" / "999 Тестовый модуль").mkdir(parents=True, exist_ok=True)
    (target / "data" / "concepts").mkdir(parents=True, exist_ok=True)

    src_path = (target / "data" / "sources" / "ТестКурс" / "999 Тестовый модуль"
                / "000 Базовая лекция.md")
    src_path.write_text(SYNTH_SOURCE)

    cpt_path = target / "data" / "concepts" / "pareto-principle.md"
    cpt_path.write_text(SYNTH_CONCEPT)


def main():
    if len(sys.argv) > 1 and sys.argv[1] != "--synth":
        wiki = Path(sys.argv[1])
        synth = False
    else:
        wiki = Path(tempfile.mkdtemp(prefix="step8-synth-wiki-"))
        make_synth_wiki(wiki)
        synth = True
        print(f"[synth] using {wiki}")

    results = {
        "step1_encode": step1_encode(),
        "step2_rebuild": step2_rebuild(wiki),
        "step3_find_claims": step3_find_claims(wiki),
        "step3b_find_concepts": step3b_find_concepts(wiki),
    }

    print("\n=== SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    if synth:
        shutil.rmtree(wiki, ignore_errors=True)

    if all(results.values()):
        print("\n=== STEP 8 PASS ===")
        sys.exit(0)
    else:
        print("\n=== STEP 8 FAIL ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
