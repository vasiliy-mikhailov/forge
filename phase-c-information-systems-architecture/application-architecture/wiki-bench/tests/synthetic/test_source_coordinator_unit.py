"""UNIT tests for source_coordinator (per ADR 0013, written BEFORE impl).

These tests codify the contract the coordinator must obey. They use a
stub `llm_callable` so the workflow can be exercised in milliseconds
without any vLLM dependency. They do NOT cover sub-agent invocation
(concept-curator); see test_source_coordinator_integration.py.

Per ADR 0010, these are explicitly UNIT tests on the workflow. The
fidelity layer for the agent + container + real LLM is the e2e test.
"""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add orchestrator/ to sys.path so we can import the module under test.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent / "orchestrator"))

# Module under test (will not import until coordinator is implemented).
# Import at top so test_collection itself fails loud if module missing.
from source_coordinator import (  # noqa: E402
    SourceCoordinator,
    StepResult,
    CoordinatorError,
    MalformedResponseError,
)


class _FakeLLM:
    """Stub LLM. Each call returns the next pre-staged response in queue.

    Records the prompts it received so tests can assert on schema use,
    sequence, retry behaviour, etc.
    """

    def __init__(self, responses):
        self._queue = list(responses)
        self.calls = []

    def __call__(self, *, prompt, response_format, max_tokens):
        self.calls.append({
            "prompt": prompt,
            "response_format": response_format,
            "max_tokens": max_tokens,
        })
        if not self._queue:
            raise RuntimeError("FakeLLM out of responses")
        nxt = self._queue.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


class CoordinatorContract(unittest.TestCase):
    """Test 1 — workflow sequence + schema enforcement."""

    def setUp(self):
        import tempfile
        self.workdir = Path(tempfile.mkdtemp(prefix="coord_unit_"))
        (self.workdir / "wiki" / "data" / "sources" / "C" / "M").mkdir(parents=True)
        self.target = self.workdir / "wiki" / "data" / "sources" / "C" / "M" / "001 stem.md"
        self.raw = self.workdir / "raw.json"
        self.raw.write_text(json.dumps({
            "info": {"language": "ru", "duration": 60.0, "extracted_at": "2026-01-01T00:00:00Z"},
            "segments": [{"id": 1, "start": 0.0, "end": 5.0, "text": "test."}],
        }))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.workdir, ignore_errors=True)

    def _staged_responses(self):
        """Stage the LLM responses for a happy-path single-source run:
        - extract_claims  → 1 claim
        - classify_claim  → NEW
        - (no factcheck)
        """
        return [
            {"claims": [{"text": "claim 1", "needs_factcheck": False}]},
            {"classifications": [{"claim_index": 1, "verdict": "NEW", "category": "test"}]},
            {"tldr": "stub TL;DR for unit test."},
            {"lecture": "stub condensed lecture for unit test."},
        ]

    def test_writes_file_at_target_path(self):
        """The coordinator MUST write source.md at the target path before
        returning success. This is the property SRC 16 violated."""
        llm = _FakeLLM(self._staged_responses())
        c = SourceCoordinator(llm=llm, workdir=self.workdir)
        result = c.process_source(
            n=1, raw_path=str(self.raw), target_path=str(self.target),
            slug="C/M/001 stem", curator=lambda *_: None,
        )
        self.assertTrue(self.target.exists(), "coordinator did not write source.md")
        self.assertGreater(self.target.stat().st_size, 0)

    def test_workflow_call_sequence(self):
        """LLM calls must happen in the documented sequence:
        extract_claims → classify_claim per claim → (factcheck per
        needs_factcheck) → compose+write."""
        llm = _FakeLLM(self._staged_responses())
        c = SourceCoordinator(llm=llm, workdir=self.workdir)
        c.process_source(
            n=1, raw_path=str(self.raw), target_path=str(self.target),
            slug="C/M/001 stem", curator=lambda *_: None,
        )
        kinds = [call["response_format"]["title"] for call in llm.calls]
        self.assertEqual(kinds, ["claims_list", "claims_batch_classification",
                                  "tldr", "lecture_condensed"])

    def test_each_call_specifies_response_schema(self):
        """Every LLM call MUST pass a `response_format` JSON schema. This
        is what removes 'agent emits malformed XML' from the failure
        space."""
        llm = _FakeLLM(self._staged_responses())
        c = SourceCoordinator(llm=llm, workdir=self.workdir)
        c.process_source(
            n=1, raw_path=str(self.raw), target_path=str(self.target),
            slug="C/M/001 stem", curator=lambda *_: None,
        )
        for call in llm.calls:
            self.assertIsNotNone(call["response_format"])
            self.assertIn("title", call["response_format"])
            self.assertIn("schema", call["response_format"])


class CoordinatorRetry(unittest.TestCase):
    """Test 2 — malformed-response handling."""

    def setUp(self):
        import tempfile
        self.workdir = Path(tempfile.mkdtemp(prefix="coord_retry_"))
        (self.workdir / "wiki" / "data" / "sources" / "C" / "M").mkdir(parents=True)
        self.target = self.workdir / "wiki" / "data" / "sources" / "C" / "M" / "001 stem.md"
        self.raw = self.workdir / "raw.json"
        self.raw.write_text(json.dumps({
            "info": {"language": "ru", "duration": 60.0, "extracted_at": "2026-01-01T00:00:00Z"},
            "segments": [{"id": 1, "start": 0.0, "end": 5.0, "text": "test."}],
        }))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.workdir, ignore_errors=True)

    def test_one_malformed_response_retries_then_succeeds(self):
        """If an LLM call returns content that doesn't match the schema,
        the coordinator retries ONCE with corrective instruction. Second
        valid response is accepted."""
        llm = _FakeLLM([
            "this is not valid JSON for claims schema",  # first → MalformedResponseError
            {"claims": [{"text": "claim 1", "needs_factcheck": False}]},  # retry → ok
            {"classifications": [{"claim_index": 1, "verdict": "NEW", "category": "test"}]},
            {"tldr": "stub TL;DR for unit test."},
            {"lecture": "stub condensed lecture for unit test."},
        ])
        c = SourceCoordinator(llm=llm, workdir=self.workdir)
        result = c.process_source(
            n=1, raw_path=str(self.raw), target_path=str(self.target),
            slug="C/M/001 stem", curator=lambda *_: None,
        )
        self.assertTrue(self.target.exists())
        # 1 extract attempt + 1 retry + 1 classify + 1 tldr + 1 lecture = 5 calls.
        self.assertEqual(len(llm.calls), 5)

    def test_two_malformed_responses_raise_coordinator_error(self):
        """Second malformed response is a hard error. No silent
        completion. This is what SRC 16 produced and what ADR 0013
        explicitly forbids."""
        llm = _FakeLLM([
            "garbage 1",
            "garbage 2",
        ])
        c = SourceCoordinator(llm=llm, workdir=self.workdir)
        with self.assertRaises(CoordinatorError) as ctx:
            c.process_source(
                n=1, raw_path=str(self.raw), target_path=str(self.target),
                slug="C/M/001 stem", curator=lambda *_: None,
            )
        # File must NOT exist on coordinator failure.
        self.assertFalse(self.target.exists(),
                         "coordinator wrote file despite hard error")


class CoordinatorTemplate(unittest.TestCase):
    """Test 3 — composed source.md must satisfy bench_grade structural
    contract (frontmatter, 5 sections, claim markers at line start)."""

    def setUp(self):
        import tempfile
        self.workdir = Path(tempfile.mkdtemp(prefix="coord_tpl_"))
        (self.workdir / "wiki" / "data" / "sources" / "C" / "M").mkdir(parents=True)
        self.target = self.workdir / "wiki" / "data" / "sources" / "C" / "M" / "001 stem.md"
        self.raw = self.workdir / "raw.json"
        self.raw.write_text(json.dumps({
            "info": {"language": "ru", "duration": 60.0, "extracted_at": "2026-01-01T00:00:00Z"},
            "segments": [{"id": 1, "start": 0.0, "end": 5.0, "text": "test."}],
        }))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.workdir, ignore_errors=True)

    def test_composed_md_has_required_sections(self):
        llm = _FakeLLM([
            {"claims": [{"text": "claim 1", "needs_factcheck": False}]},
            {"classifications": [{"claim_index": 1, "verdict": "NEW", "category": "test"}]},
            {"tldr": "stub TL;DR for unit test."},
            {"lecture": "stub condensed lecture for unit test."},
        ])
        c = SourceCoordinator(llm=llm, workdir=self.workdir)
        c.process_source(
            n=1, raw_path=str(self.raw), target_path=str(self.target),
            slug="C/M/001 stem", curator=lambda *_: None,
        )
        body = self.target.read_text(encoding="utf-8")
        for required in ["## TL;DR", "## Лекция сжато",
                         "## Claims", "## New ideas", "## All ideas"]:
            self.assertIn(required, body, f"section {required!r} missing")

    def test_each_claim_marker_at_line_start(self):
        """Per the prompt change earlier this week, [NEW]/[REPEATED]
        markers must lead the claim line, not trail it. This is a
        coordinator-side template responsibility now (no LLM agency)."""
        llm = _FakeLLM([
            {"claims": [{"text": "first claim", "needs_factcheck": False}]},
            {"classifications": [{"claim_index": 1, "verdict": "NEW", "category": "test"}]},
            {"tldr": "stub TL;DR for unit test."},
            {"lecture": "stub condensed lecture for unit test."},
        ])
        c = SourceCoordinator(llm=llm, workdir=self.workdir)
        c.process_source(
            n=1, raw_path=str(self.raw), target_path=str(self.target),
            slug="C/M/001 stem", curator=lambda *_: None,
        )
        body = self.target.read_text(encoding="utf-8")
        # Find a claim line; it must start with `1. [NEW]` (or similar).
        import re
        m = re.search(r"^1\. \[NEW\]", body, re.M)
        self.assertIsNotNone(m, "claim line does not lead with [NEW]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
