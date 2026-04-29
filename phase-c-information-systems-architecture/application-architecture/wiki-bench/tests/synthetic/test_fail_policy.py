"""Synth tests for the orchestrator's per-source fail-policy.

Tests two policies:
  - fail_fast (default for v5/G1/G2/G3): stop on first verify-fail.
  - continue (new for K1): mark fail in state, continue to next.

The unit under test is `record_per_source_outcome(state, n, slug,
verify_result, policy)` — a small helper extracted from main()'s
per-source loop. Returns "stop" if the loop should break,
"continue" otherwise. Records to state in either case.
"""
from __future__ import annotations
import ast
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORCH = HERE.parent.parent / "orchestrator"


def _extract_function(name: str) -> str:
    src = (ORCH / "run-d8-pilot.py").read_text()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return "\n".join(src.splitlines()[node.lineno - 1:node.end_lineno])
    raise RuntimeError(f"function {name!r} not in run-d8-pilot.py")


def _load_helper():
    """Load record_per_source_outcome() in isolation."""
    ns = {"__name__": "fail_policy_test"}
    code = _extract_function("record_per_source_outcome")
    exec(compile(code, str(ORCH / "run-d8-pilot.py"), "exec"), ns)
    return ns["record_per_source_outcome"]


class FailPolicyTests(unittest.TestCase):

    def setUp(self):
        self.fn = _load_helper()
        self.state = []

    # 1. fail_fast policy — first verify-fail returns "stop".
    def test_1_fail_fast_stops_on_fail(self):
        decision = self.fn(self.state, n=2, slug="course/mod/002 src",
                           verify_result={"verified": "fail",
                                          "violations": ["foo"]},
                           policy="fail_fast")
        self.assertEqual(decision, "stop")
        self.assertEqual(len(self.state), 1)
        self.assertEqual(self.state[0]["verify"]["verified"], "fail")
        self.assertEqual(self.state[0]["stopped"], "verify_fail")

    # 2. continue policy — verify-fail returns "continue".
    def test_2_continue_keeps_going_on_fail(self):
        decision = self.fn(self.state, n=3, slug="course/mod/003 src",
                           verify_result={"verified": "fail",
                                          "violations": ["foo"]},
                           policy="continue")
        self.assertEqual(decision, "continue")
        self.assertEqual(len(self.state), 1)
        self.assertEqual(self.state[0]["verify"]["verified"], "fail")
        # Even with continue, we still record the failure for post-pilot grading.
        self.assertEqual(self.state[0].get("stopped"), "verify_fail")

    # 3. Either policy returns "continue" on verify=ok.
    def test_3_ok_continues_under_fail_fast(self):
        decision = self.fn(self.state, n=0, slug="course/mod/000 src",
                           verify_result={"verified": "ok"},
                           policy="fail_fast")
        self.assertEqual(decision, "continue")
        self.assertEqual(self.state[0]["verify"]["verified"], "ok")

    def test_4_ok_continues_under_continue(self):
        decision = self.fn(self.state, n=0, slug="course/mod/000 src",
                           verify_result={"verified": "ok"},
                           policy="continue")
        self.assertEqual(decision, "continue")

    # 5. Sequence test: simulate a 4-source pilot where source 2 fails.
    def test_5_sequence_continue_processes_all_4(self):
        results = [
            ("000 a", {"verified": "ok"}),
            ("001 b", {"verified": "ok"}),
            ("002 c", {"verified": "fail", "violations": ["whatever"]}),
            ("003 d", {"verified": "ok"}),
        ]
        decisions = []
        for i, (slug, v) in enumerate(results):
            d = self.fn(self.state, n=i, slug=f"c/m/{slug}",
                        verify_result=v, policy="continue")
            decisions.append(d)
            if d == "stop":
                break
        self.assertEqual(decisions, ["continue", "continue", "continue", "continue"])
        self.assertEqual(len(self.state), 4)
        verifies = [s["verify"]["verified"] for s in self.state]
        self.assertEqual(verifies, ["ok", "ok", "fail", "ok"])

    def test_6_sequence_fail_fast_stops_after_2(self):
        results = [
            ("000 a", {"verified": "ok"}),
            ("001 b", {"verified": "ok"}),
            ("002 c", {"verified": "fail", "violations": ["whatever"]}),
            ("003 d", {"verified": "ok"}),
        ]
        decisions = []
        for i, (slug, v) in enumerate(results):
            d = self.fn(self.state, n=i, slug=f"c/m/{slug}",
                        verify_result=v, policy="fail_fast")
            decisions.append(d)
            if d == "stop":
                break
        self.assertEqual(decisions, ["continue", "continue", "stop"])
        self.assertEqual(len(self.state), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
