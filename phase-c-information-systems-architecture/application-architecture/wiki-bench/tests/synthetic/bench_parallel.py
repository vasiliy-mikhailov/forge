"""Sweep _MAX_PARALLEL ∈ {5, 10, 15, 20} on a single real K1 source.

Runs the coordinator's full per-source pipeline at each setting and
reports per-phase + total wall time. Identifies the sweet spot before
vLLM concurrency saturates and added workers stop helping.

Run inside the bench container with the K1 v2 raw repo bind-mounted
at /raw_input. Requires LLM_BASE_URL/API_KEY/MODEL env vars.
"""
from __future__ import annotations
import importlib
import json
import os
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, "/opt/forge")
import litellm


# Source for the benchmark — pick a real, content-rich K1 source so
# the parallelism actually exercises both extract and classify phases.
# 008 "Кто такой этот загадочный мистер Фрейд?" is biographical content
# with ~50-100 claims; first 100 segments give us 9 chunks at 8K each.
COURSE = "Психолог-консультант"
MODULE = "000 Путеводитель по программе"
STEM = "000 Знакомство с программой «Психолог-консультант»"
N_SEGMENTS = 5000  # take all segments; this source has the richest content

# Sweep settings — sweep wider, higher values let us find vLLM saturation.
PARALLEL_VALUES = [13, 14, 15, 16, 17]
ITERATIONS_PER = 2  # raise for tighter measurement; cost = N×wall


def _make_real_llm(model, base_url, api_key):
    def llm(*, prompt, response_format, max_tokens):
        rf = {
            "type": "json_schema",
            "json_schema": {
                "name": response_format["title"],
                "schema": response_format["schema"],
                "strict": True,
            },
        }
        try:
            resp = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format=rf,
                max_tokens=max_tokens,
                api_base=base_url,
                api_key=api_key,
                timeout=180.0,
            )
        except Exception as e:
            return f"litellm error: {type(e).__name__}: {e}"
        content = resp.choices[0].message.content
        try:
            return json.loads(content)
        except Exception:
            return content
    return llm


def _stub_curator(workdir):
    concepts_dir = workdir / "wiki" / "data" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    def curator(concept_slug, source_slug):
        path = concepts_dir / f"{concept_slug}.md"
        if path.exists():
            return
        path.write_text(
            f"---\nslug: {concept_slug}\n---\n# {concept_slug}\n",
            encoding="utf-8",
        )
    return curator


def _build_workspace(seg_count):
    workdir = Path(tempfile.mkdtemp(prefix="bench_par_", dir="/workspace"))
    course_nfc = unicodedata.normalize("NFC", COURSE)
    module_nfc = unicodedata.normalize("NFC", MODULE)
    stem_nfc = unicodedata.normalize("NFC", STEM)

    # Pull from /raw_input/data/<course>/<module>/<stem>/raw.json (NFD on disk).
    candidates = list(Path("/raw_input/data").glob(f"*/*/*"))
    src = None
    for c in candidates:
        cnfc = unicodedata.normalize("NFC", c.name)
        if cnfc == stem_nfc and unicodedata.normalize("NFC", c.parent.name) == module_nfc:
            src = c / "raw.json"
            break
    if src is None or not src.exists():
        raise RuntimeError(f"raw.json not found for {STEM}")

    raw = json.loads(src.read_text(encoding="utf-8"))
    compacted = {
        "info": dict(raw["info"]),
        "segments": raw["segments"][:seg_count],
    }
    raw_dir = workdir / "raw" / "data" / course_nfc / module_nfc / stem_nfc
    raw_dir.mkdir(parents=True)
    raw_path = raw_dir / "raw.json"
    raw_path.write_text(json.dumps(compacted, ensure_ascii=False),
                        encoding="utf-8")

    target_path = workdir / "wiki" / "data" / "sources" / course_nfc / module_nfc / f"{stem_nfc}.md"
    target_path.parent.mkdir(parents=True)
    return workdir, raw_path, target_path, f"{course_nfc}/{module_nfc}/{stem_nfc}"


def run_one(parallel_n, llm, raw_path, target_path, slug):
    """Reload source_coordinator with this _MAX_PARALLEL, then run."""
    os.environ["D8_PILOT_MAX_PARALLEL"] = str(parallel_n)
    # Force re-import so the constant picks up the env value.
    if "source_coordinator" in sys.modules:
        del sys.modules["source_coordinator"]
    import source_coordinator
    importlib.reload(source_coordinator)

    workdir = target_path.parent.parent.parent.parent.parent  # back to root
    # Each iteration uses a fresh target so file_exists doesn't short-circuit.
    target_path.unlink(missing_ok=True)

    coord = source_coordinator.SourceCoordinator(llm=llm, workdir=workdir)
    curator = _stub_curator(workdir)

    t0 = time.monotonic()
    result = coord.process_source(
        n=0, raw_path=str(raw_path),
        target_path=str(target_path),
        slug=slug, curator=curator,
        retriever=None,  # skip retrieval to isolate parallelism gains
    )
    wall = time.monotonic() - t0
    return wall, result


def main():
    base_url = os.environ.get("LLM_BASE_URL", "https://inference.mikhailov.tech/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8")
    if not api_key:
        print("LLM_API_KEY missing; abort"); sys.exit(2)

    llm = _make_real_llm(model, base_url, api_key)

    print(f"=== bench_parallel.py — sweep {PARALLEL_VALUES} on {STEM!r}")
    print(f"=== model={model} base_url={base_url}")
    print(f"=== {N_SEGMENTS} segments, retriever disabled\n")

    results = []
    for p in PARALLEL_VALUES:
        # Fresh workspace per run so output files don't influence the next.
        workdir, raw_path, target_path, slug = _build_workspace(N_SEGMENTS)
        try:
            for it in range(ITERATIONS_PER):
                print(f"\n→ parallel={p}, iter={it+1}/{ITERATIONS_PER}")
                wall, result = run_one(p, llm, raw_path, target_path, slug)
                ok = "ok" if target_path.exists() else "FILE NOT WRITTEN"
                print(f"  parallel={p:>2}  wall={wall:6.1f}s  "
                      f"claims={result.claims_total:>3}  "
                      f"NEW={result.claims_NEW:>3}  "
                      f"REPEATED={result.claims_REPEATED:>3}  "
                      f"CF={result.claims_CF:>2}  "
                      f"concepts={result.concepts_curated:>3}  "
                      f"{ok}")
                results.append({
                    "parallel": p, "iter": it + 1, "wall_s": wall,
                    "claims": result.claims_total,
                    "concepts": result.concepts_curated,
                    "ok": target_path.exists(),
                })
        finally:
            import shutil
            shutil.rmtree(workdir, ignore_errors=True)

    print("\n=== summary (per-iteration) ===")
    print(f"{'parallel':>8}  {'iter':>4}  {'wall (s)':>10}  {'claims':>6}  "
          f"{'s/claim':>9}")
    for r in results:
        spc = r["wall_s"] / r["claims"] if r["claims"] else float("inf")
        print(f"{r['parallel']:>8}  {r['iter']:>4}  {r['wall_s']:>10.1f}  "
              f"{r['claims']:>6}  {spc:>9.3f}")

    print("\n=== summary (averaged across iterations) ===")
    print(f"{'parallel':>8}  {'mean wall':>10}  {'mean claims':>11}  "
          f"{'mean s/claim':>12}")
    by_p = {}
    for r in results:
        by_p.setdefault(r["parallel"], []).append(r)
    rows = []
    for p in sorted(by_p):
        rs = by_p[p]
        wall_avg = sum(x["wall_s"] for x in rs) / len(rs)
        claims_avg = sum(x["claims"] for x in rs) / len(rs)
        spc_avg = sum(
            x["wall_s"] / x["claims"] for x in rs if x["claims"]
        ) / len(rs)
        rows.append((p, wall_avg, claims_avg, spc_avg))
        print(f"{p:>8}  {wall_avg:>10.1f}  {claims_avg:>11.1f}  "
              f"{spc_avg:>12.3f}")

    if rows:
        best = min(rows, key=lambda r: r[3])
        print(f"\n→ sweet spot: parallel={best[0]}, "
              f"mean s/claim={best[3]:.3f}")


if __name__ == "__main__":
    main()
