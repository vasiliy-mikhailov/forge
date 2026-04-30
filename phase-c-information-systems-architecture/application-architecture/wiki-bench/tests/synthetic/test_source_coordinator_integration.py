"""INTEGRATION tests for source_coordinator (per ADR 0013 + ADR 0010).

Production call path the integration test exercises:
  source_coordinator.process_source()
    → llm callable (mocked here for determinism)
    → composes source.md via Python template
    → writes source.md to disk
    → invokes curator callable per concept (stub here writes concept.md)
  → bench_grade.py grades the file (REAL, baked into the image)

Test fidelity (per ADR 0010):
  - Process boundary: REAL bench container (kurpatov-wiki-bench:1.17.0-d8-cal).
  - Filesystem stack: REAL /workspace bind mount.
  - Python interpreter: REAL 3.12 + same SDK baked into image.
  - bench_grade.py: REAL — the grader the production orchestrator uses.
  - Encoding: REAL Cyrillic stems (per ADR 0011, NFC canonical).
Skipped: vLLM (mocked llm callable) and OpenHands sub-agent for the
  concept-curator (replaced by a stub that just writes a concept.md
  with the canonical skill-v2 template). The e2e test exercises both.

Run via run_coordinator_integration_tests.sh which rebuilds the bench
image (per ADR 0012-phase-g) and spawns this file inside it.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, "/opt/forge")
from source_coordinator import (
    SourceCoordinator,
    CoordinatorError,
    MalformedResponseError,
)


BENCH_GRADE = "/opt/forge/bench_grade.py"


def _stub_curator(workdir: Path):
    """Return a curator callable that writes a minimal concept file
    matching the skill-v2 template — enough for bench_grade to find
    the concept-touched cross-reference and not flag it as dangling.
    """
    concepts_dir = workdir / "wiki" / "data" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    def curator(concept_slug: str, source_slug: str):
        path = concepts_dir / f"{concept_slug}.md"
        body = (
            "---\n"
            f"slug: {concept_slug}\n"
            f"first_introduced_in: {source_slug}\n"
            f"touched_by:\n  - {source_slug}\n"
            "---\n"
            f"# {concept_slug}\n\n"
            "## Definition\n\n"
            f"Stub concept for integration test.\n\n"
            "## Contributions by source\n\n"
            f"### {source_slug}\n\n"
            "Stub contribution.\n"
        )
        # Idempotent: only write if not present (multi-source runs).
        if not path.exists():
            path.write_text(body, encoding="utf-8")
    return curator


class _StagedLLM:
    """LLM stub for the coordinator. Returns pre-staged responses in
    order. Records each call for assertions."""

    def __init__(self, responses):
        self._queue = list(responses)
        self.calls = []

    def __call__(self, *, prompt, response_format, max_tokens):
        self.calls.append({
            "schema": response_format["title"],
            "prompt_len": len(prompt),
            "max_tokens": max_tokens,
        })
        if not self._queue:
            raise RuntimeError(
                f"_StagedLLM out of responses; "
                f"already served {len(self.calls)} calls"
            )
        return self._queue.pop(0)


class _Fixture:
    """Build a per-test workspace under /workspace/<unique-dir> with the
    raw repo + wiki repo skeleton the coordinator expects."""

    def __init__(self):
        self.workdir = Path(tempfile.mkdtemp(prefix="coord_int_", dir="/workspace"))
        # Raw repo layout (mirrors production).
        self.course = "Психолог-консультант"
        self.module = "001 Тестовый модуль"
        self.stem = "002 Тестовая лекция"  # Cyrillic + ASCII digits
        self.slug = f"{self.course}/{self.module}/{self.stem}"
        raw_dir = self.workdir / "raw" / "data" / self.course / self.module / self.stem
        raw_dir.mkdir(parents=True, exist_ok=True)
        self.raw_path = raw_dir / "raw.json"
        # Two-segment compacted raw — same shape as production.
        self.raw_path.write_text(json.dumps({
            "info": {
                "language": "ru", "duration": 60.0,
                "extractor": "whisper", "model": "large-v3",
                "extracted_at": "2026-04-30T00:00:00Z",
                "transcribed_at": "2026-04-30T00:00:00Z",
                "diarized": False,
                "source_path": "/workspace/x.mp3",
            },
            "segments": [
                {"id": 1, "start": 0.0, "end": 5.0, "speaker": None,
                 "text": "Тестовый сегмент один.", "words": []},
                {"id": 2, "start": 5.0, "end": 10.0, "speaker": None,
                 "text": "Тестовый сегмент два.", "words": []},
            ],
        }, ensure_ascii=False), encoding="utf-8")
        # Wiki repo skeleton.
        wiki_sources = self.workdir / "wiki" / "data" / "sources" / self.course / self.module
        wiki_sources.mkdir(parents=True, exist_ok=True)
        self.target_path = wiki_sources / f"{self.stem}.md"

    def cleanup(self):
        import shutil
        shutil.rmtree(self.workdir, ignore_errors=True)


def _bench_grade(workdir: Path, module_subdir: str, stem: str) -> dict:
    """Run bench_grade.py against a single source. Returns the parsed
    JSON. This is THE production grader, baked into the bench image."""
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


class CoordinatorIntegration(unittest.TestCase):

    def setUp(self):
        self.fx = _Fixture()

    def tearDown(self):
        self.fx.cleanup()

    # 1. Happy path — single claim, no factcheck. The composed source.md
    # must pass bench_grade verified=ok.
    def test_1_happy_path_passes_bench_grade(self):
        llm = _StagedLLM([
            {"claims": [{"text": "Тестовое утверждение один.",
                         "needs_factcheck": False}]},
            {"verdict": "NEW", "category": "test-category-one"},
        ])
        curator = _stub_curator(self.fx.workdir)
        c = SourceCoordinator(llm=llm, workdir=self.fx.workdir)
        result = c.process_source(
            n=2, raw_path=str(self.fx.raw_path),
            target_path=str(self.fx.target_path),
            slug=self.fx.slug, curator=curator,
        )
        self.assertTrue(self.fx.target_path.exists())
        graded = _bench_grade(self.fx.workdir,
                              f"{self.fx.course}/{self.fx.module}",
                              self.fx.stem)
        self.assertEqual(graded.get("verified"), "ok",
                         f"bench_grade rejected: {graded.get('violations')}")
        self.assertEqual(graded["metrics"]["claims_total"], 1)
        self.assertEqual(graded["metrics"]["claims_NEW"], 1)
        self.assertEqual(result.concepts_curated, 1)

    # 2. Multiple claims with mixed verdicts; one needs fact-check.
    def test_2_multi_claim_mixed_verdicts(self):
        llm = _StagedLLM([
            {"claims": [
                {"text": "Утверждение А.", "needs_factcheck": False},
                {"text": "Утверждение Б.", "needs_factcheck": True},
                {"text": "Утверждение В.", "needs_factcheck": False},
            ]},
            {"verdict": "NEW", "category": "cat-a"},
            {"verdict": "REPEATED", "category": "cat-b",
             "from_slug": "Психолог-консультант/000/000 prior"},
            {"verdict": "NEW", "category": "cat-c"},
            # Fact-check for claim B (needs_factcheck=True).
            {"marker": "NEW", "url": "https://example.com",
             "notes": "Verified against public source."},
        ])
        curator = _stub_curator(self.fx.workdir)
        c = SourceCoordinator(llm=llm, workdir=self.fx.workdir)
        result = c.process_source(
            n=2, raw_path=str(self.fx.raw_path),
            target_path=str(self.fx.target_path),
            slug=self.fx.slug, curator=curator,
        )
        graded = _bench_grade(self.fx.workdir,
                              f"{self.fx.course}/{self.fx.module}",
                              self.fx.stem)
        self.assertEqual(graded.get("verified"), "ok",
                         f"bench_grade rejected: {graded.get('violations')}")
        self.assertEqual(graded["metrics"]["claims_total"], 3)
        self.assertEqual(graded["metrics"]["claims_NEW"], 2)
        self.assertEqual(graded["metrics"]["claims_REPEATED"], 1)
        # Three distinct categories → three concepts curated.
        self.assertEqual(result.concepts_curated, 3)

    # 3. Malformed-response retry path: first extract response is junk,
    # second is valid. Final source.md still verified=ok.
    def test_3_malformed_extract_retries_then_succeeds(self):
        llm = _StagedLLM([
            "garbage that won't validate",  # first attempt, malformed
            {"claims": [{"text": "Утверждение.",
                         "needs_factcheck": False}]},  # retry, valid
            {"verdict": "NEW", "category": "retry-cat"},
        ])
        curator = _stub_curator(self.fx.workdir)
        c = SourceCoordinator(llm=llm, workdir=self.fx.workdir)
        c.process_source(
            n=2, raw_path=str(self.fx.raw_path),
            target_path=str(self.fx.target_path),
            slug=self.fx.slug, curator=curator,
        )
        graded = _bench_grade(self.fx.workdir,
                              f"{self.fx.course}/{self.fx.module}",
                              self.fx.stem)
        self.assertEqual(graded.get("verified"), "ok",
                         f"bench_grade rejected: {graded.get('violations')}")
        # 1 extract retry + 1 extract success + 1 classify = 3 calls.
        self.assertEqual(len(llm.calls), 3)

    # 4. Two consecutive malformed responses → CoordinatorError, NO file
    # written. This is the property SRC 17 (the "shape of a closing tag"
    # incident) violated.
    def test_4_two_malformed_responses_raises_no_file(self):
        llm = _StagedLLM(["garbage1", "garbage2"])
        curator = _stub_curator(self.fx.workdir)
        c = SourceCoordinator(llm=llm, workdir=self.fx.workdir)
        with self.assertRaises(MalformedResponseError):
            c.process_source(
                n=2, raw_path=str(self.fx.raw_path),
                target_path=str(self.fx.target_path),
                slug=self.fx.slug, curator=curator,
            )
        self.assertFalse(self.fx.target_path.exists(),
                         "coordinator wrote source.md despite hard error")


if __name__ == "__main__":
    unittest.main(verbosity=2)
