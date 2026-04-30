"""E2E tests for source_coordinator (per ADR 0013, highest fidelity layer).

Production call path the e2e test exercises:
  source_coordinator.process_source()
    → REAL vLLM via litellm with response_format=json_schema
       (per-step structured calls — the structural answer to the
        agency-fragility class of bugs)
    → composes source.md via Python template
    → writes source.md
    → invokes curator (stub here writes concept.md;
       the real concept-curator agent integration is a separate test)
  → bench_grade.py grades each file (REAL, baked into the image)

Test fidelity (per ADR 0010):
  - Process boundary: REAL bench container.
  - LLM: REAL vLLM (Qwen3.6-27B-FP8) at INFERENCE_BASE_URL with
    json_schema constrained decoding. This is the layer where the
    OLD source-author agent's "wrong tool-call format" bug used to
    surface; the coordinator's response_format eliminates that class.
  - Filesystem: REAL /workspace bind-mount with NFC-normalised raw.
  - bench_grade.py: REAL.
  - Encoding: REAL Cyrillic stems from the K1 raw repo.
Skipped: real concept-curator OpenHands agent (next test layer).

Run via run_coordinator_e2e_tests.sh.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, "/opt/forge")
from source_coordinator import (
    SourceCoordinator,
    CoordinatorError,
    MalformedResponseError,
)


BENCH_GRADE = "/opt/forge/bench_grade.py"


def _make_real_llm():
    """Return a callable that talks to vLLM via litellm with
    response_format=json_schema. The coordinator passes
    (prompt, response_format, max_tokens); we translate to the
    OpenAI chat-completions format vLLM speaks."""
    import litellm

    base_url = os.environ.get("LLM_BASE_URL", "https://inference.mikhailov.tech/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8")

    def llm(*, prompt, response_format, max_tokens):
        # Convert coordinator's schema dict (title, schema) into
        # OpenAI's response_format=json_schema shape.
        rf = {
            "type": "json_schema",
            "json_schema": {
                "name": response_format["title"],
                "schema": response_format["schema"],
                "strict": True,
            },
        }
        t0 = time.monotonic()
        resp = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=rf,
            max_tokens=max_tokens,
            api_base=base_url,
            api_key=api_key,
            timeout=120.0,
        )
        dt = time.monotonic() - t0
        content = resp.choices[0].message.content
        print(f"  [llm] schema={response_format['title']!r} "
              f"dt={dt:.1f}s out_chars={len(content)}", flush=True)
        # Coordinator expects parsed dict; let it handle parse errors
        # so its retry-once-then-fail path runs.
        try:
            return json.loads(content)
        except Exception:
            return content  # raw string → coordinator marks malformed
    return llm


def _stub_curator(workdir: Path):
    """Same stub as integration test — writes a minimal concept.md so
    bench_grade's cross-references don't dangle."""
    concepts_dir = workdir / "wiki" / "data" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    written = []

    def curator(concept_slug: str, source_slug: str):
        path = concepts_dir / f"{concept_slug}.md"
        if path.exists():
            return
        body = (
            "---\n"
            f"slug: {concept_slug}\n"
            f"first_introduced_in: {source_slug}\n"
            f"touched_by:\n  - {source_slug}\n"
            "---\n"
            f"# {concept_slug}\n\n"
            "## Definition\n\n"
            "Stub concept (e2e test layer; concept-curator agent "
            "integration is a separate fidelity layer).\n\n"
            "## Contributions by source\n\n"
            f"### {source_slug}\n\n"
            "Stub contribution.\n"
        )
        path.write_text(body, encoding="utf-8")
        written.append(concept_slug)
    return curator, written


def _bench_grade(workdir: Path, module_subdir: str, stem: str) -> dict:
    cmd = [
        "python3", BENCH_GRADE,
        str(workdir / "wiki"),
        "--single-source-json",
        "--single-source-stem", stem,
        "--module-subdir", module_subdir,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(
            f"bench_grade failed: rc={r.returncode}, "
            f"stderr={r.stderr[:400]!r}, stdout={r.stdout[:400]!r}"
        )
    return json.loads(r.stdout)


class _RealFixture:
    """Build a workspace with a REAL raw.json compacted to a few
    segments. Mirrors build_e2e_real_fixture.py's NFC normalisation.
    """

    def __init__(self, source_subdir, source_stem, n_segments=5):
        import unicodedata

        self.workdir = Path(tempfile.mkdtemp(prefix="coord_e2e_", dir="/workspace"))
        self.course = "Психолог-консультант"
        self.module = source_subdir
        self.stem = source_stem
        self.slug = f"{self.course}/{self.module}/{self.stem}"

        # Source must already exist in /tmp/k1-pilot/raw or similar.
        # E2E uses bind-mounted real raw repo. We point at the workspace's
        # own staged raw.json.
        # The runner script builds the staging from /tmp/k1-v2-pilot/raw or
        # a known fixture; here we just compact whatever's at the
        # documented input path.
        candidates = [
            Path("/raw_input/data") / self.course / self.module / self.stem,
            Path("/tmp/k1-v2-pilot/raw/data") / self.course / self.module / self.stem,
            Path("/tmp/k1-pilot/raw/data") / self.course / self.module / self.stem,
        ]
        src = next((c for c in candidates if c.exists()), None)
        if src is None:
            raise unittest.SkipTest(
                f"raw source not found at any of {candidates}; "
                f"runner must bind-mount raw repo at /raw_input"
            )
        # Resolve actual NFD-encoded directory entries through os.listdir
        # roundtrip (per ADR 0011 M1 — but here we're reading the unmounted
        # raw repo, then normalising on the way out).

        raw_data = json.loads((src / "raw.json").read_text(encoding="utf-8"))
        compacted = {
            "info": dict(raw_data["info"]),
            "segments": raw_data["segments"][:n_segments],
        }
        compacted["info"]["__fixture__"] = "coord-e2e-compacted"

        # Stage compacted raw under the workdir, NFC-normalised.
        course_nfc = unicodedata.normalize("NFC", self.course)
        module_nfc = unicodedata.normalize("NFC", self.module)
        stem_nfc = unicodedata.normalize("NFC", self.stem)
        raw_dir = self.workdir / "raw" / "data" / course_nfc / module_nfc / stem_nfc
        raw_dir.mkdir(parents=True, exist_ok=True)
        self.raw_path = raw_dir / "raw.json"
        self.raw_path.write_text(
            json.dumps(compacted, ensure_ascii=False),
            encoding="utf-8",
        )
        self.slug = f"{course_nfc}/{module_nfc}/{stem_nfc}"

        # Wiki target.
        wiki_sources = self.workdir / "wiki" / "data" / "sources" / course_nfc / module_nfc
        wiki_sources.mkdir(parents=True, exist_ok=True)
        self.target_path = wiki_sources / f"{stem_nfc}.md"
        self.module_subdir = f"{course_nfc}/{module_nfc}"

    def cleanup(self):
        import shutil
        shutil.rmtree(self.workdir, ignore_errors=True)


class CoordinatorE2E(unittest.TestCase):
    """E2E: real vLLM, real bench_grade, real Cyrillic source."""

    @classmethod
    def setUpClass(cls):
        if not os.environ.get("LLM_API_KEY"):
            raise unittest.SkipTest("LLM_API_KEY not set")

    # 1. Compacted real source 008 from K1 module 001 — biographical
    # content about Freud, definitely has empirical claims to extract.
    # 30 segments ~= first 5 minutes of audio. Asserts:
    #   - bench_grade accepts the produced source.md
    #   - claims_total >= 3 (the LLM actually extracted content,
    #     the coordinator didn't just succeed on emptiness)
    def test_1_real_source_with_claims_passes(self):
        fx = _RealFixture(
            source_subdir="001 Глубинная психология и психодиагностика в консультировании",
            source_stem="008 2.1 Кто такой этот загадочный мистер Фрейд?",
            n_segments=30,
        )
        try:
            llm = _make_real_llm()
            curator, concept_log = _stub_curator(fx.workdir)
            c = SourceCoordinator(llm=llm, workdir=fx.workdir)
            print(f"\n→ processing {fx.slug!r}", flush=True)
            t0 = time.monotonic()
            result = c.process_source(
                n=0, raw_path=str(fx.raw_path),
                target_path=str(fx.target_path),
                slug=fx.slug, curator=curator,
            )
            dt = time.monotonic() - t0
            print(f"  done in {dt:.1f}s; "
                  f"claims={result.claims_total} "
                  f"NEW={result.claims_NEW} "
                  f"REPEATED={result.claims_REPEATED} "
                  f"CF={result.claims_CF} "
                  f"concepts={result.concepts_curated}",
                  flush=True)
            self.assertTrue(fx.target_path.exists())
            graded = _bench_grade(fx.workdir, fx.module_subdir, fx.stem)
            self.assertEqual(
                graded.get("verified"), "ok",
                f"bench_grade rejected: {graded.get('violations')}",
            )
            # Meaningful-output assertion: a 30-segment Freud biographical
            # transcript should produce at least 3 claims and at least 1
            # concept. If this fires, the LLM returned an effectively empty
            # response that nevertheless passed schema validation —
            # signal we'd otherwise miss.
            self.assertGreaterEqual(
                result.claims_total, 3,
                f"LLM extracted only {result.claims_total} claims from 30 "
                f"segments — likely a prompt or schema problem, not a "
                f"coordinator bug",
            )
            self.assertGreaterEqual(result.concepts_curated, 1)
        finally:
            fx.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
