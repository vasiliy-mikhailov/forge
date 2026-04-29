"""Synth tests for `verify_source` (TDD-style).

Extracts only the verify_source function from run-d8-pilot.py
(by AST surgery so the rest of the module's heavy OpenHands SDK
imports aren't pulled in), execs it in a controlled namespace
that supplies stdlib + WORKDIR + BENCH_GRADE stubs, and runs the
function against synthetic file fixtures.

Run on host: ~30s end-to-end, no docker/vllm/agent.
"""
from __future__ import annotations
import ast
import json
import os
import sys
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORCH = HERE.parent.parent / "orchestrator"


def _extract_verify_source_text() -> str:
    """Return just the source of `def verify_source(...)` from
    run-d8-pilot.py, parsed via AST so we don't need the surrounding
    imports."""
    src = (ORCH / "run-d8-pilot.py").read_text()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "verify_source":
            start = node.lineno - 1  # ast lines are 1-indexed
            end = node.end_lineno     # exclusive in source split
            return "\n".join(src.splitlines()[start:end])
    raise RuntimeError("verify_source function not found in run-d8-pilot.py")


def _load_verify_source(workdir: Path, bench_grade_path: str):
    """Build a namespace with WORKDIR/BENCH_GRADE/stdlib bound, exec
    verify_source's text into it, return the function."""
    ns = {
        "__name__": "verify_source_test_module",
        "WORKDIR": workdir,
        "BENCH_GRADE": bench_grade_path,
        "Path": Path,
        "subprocess": __import__("subprocess"),
        "json": json,
        "time": time,
    }
    code = _extract_verify_source_text()
    exec(compile(code, str(ORCH / "run-d8-pilot.py"), "exec"), ns)
    return ns["verify_source"]


class VerifySourceTests(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmpdir = Path(tempfile.mkdtemp(prefix="verify_test_"))
        self.workdir = self.tmpdir / "workspace"
        (self.workdir / "wiki" / "data" / "sources").mkdir(parents=True)
        # Stub bench_grade: always returns verified=ok, no violations.
        # The unit under test is verify_source's poll, not bench_grade.
        self.stub = self.tmpdir / "stub_bench_grade.py"
        self.stub.write_text(
            "import json, sys\n"
            "print(json.dumps({'verified': 'ok', 'violations': []}))\n"
        )
        self.verify_source = _load_verify_source(self.workdir, str(self.stub))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _put_source(self, module_subdir: str, stem: str, body: str = "frontmatter\nbody\n"):
        d = self.workdir / "wiki" / "data" / "sources" / module_subdir
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{stem}.md").write_text(body, encoding="utf-8")

    # 1. ASCII existing file — sanity.
    def test_1_ascii_existing_file(self):
        self._put_source("course/module-a", "001 source")
        v = self.verify_source(n=1, original_n=1,
                                module_subdir="course/module-a",
                                stem="001 source")
        self.assertEqual(v.get("verified"), "ok", v)

    # 2. Cyrillic + curly «» path (K1 module 000 SRC 0).
    def test_2_cyrillic_existing_file(self):
        module_subdir = "Психолог-консультант/000 Путеводитель по программе"
        stem = "000 Знакомство с программой «Психолог-консультант»"
        self._put_source(module_subdir, stem)
        v = self.verify_source(n=0, original_n=0,
                                module_subdir=module_subdir, stem=stem)
        self.assertEqual(v.get("verified"), "ok", v)

    # 3. File appears 1s after polling starts.
    def test_3_file_appears_after_1s(self):
        module_subdir = "course/module"
        stem = "002 deferred"
        threading.Thread(
            target=lambda: (time.sleep(1.0), self._put_source(module_subdir, stem)),
            daemon=True,
        ).start()
        t0 = time.monotonic()
        v = self.verify_source(n=2, original_n=2,
                                module_subdir=module_subdir, stem=stem)
        elapsed = time.monotonic() - t0
        self.assertEqual(v.get("verified"), "ok", v)
        self.assertLess(elapsed, 5.0, f"detected after {elapsed:.1f}s, want <5s")

    # 4. File appears 25s after polling starts (within 30s deadline,
    #    well below the 90s production default).
    def test_4_file_appears_after_25s(self):
        module_subdir = "course/module"
        stem = "003 slow"
        threading.Thread(
            target=lambda: (time.sleep(25.0), self._put_source(module_subdir, stem)),
            daemon=True,
        ).start()
        v = self.verify_source(n=3, original_n=3,
                                module_subdir=module_subdir, stem=stem,
                                deadline_secs=30.0)
        self.assertEqual(v.get("verified"), "ok", v)

    # 5. File never appears — must fail with diagnostic. Use a short
    #    deadline (3s) so the test runs fast.
    def test_5_file_never_appears(self):
        v = self.verify_source(n=4, original_n=4,
                                module_subdir="course/module",
                                stem="004 missing",
                                deadline_secs=3.0)
        self.assertEqual(v.get("verified"), "fail")
        joined = " ".join(str(x) for x in (v.get("violations") or []))
        self.assertIn("did not appear", joined, joined)

    # 6. File grows during stability poll — must wait until stable.
    def test_6_file_size_growing(self):
        module_subdir = "course/module"
        stem = "005 growing"
        d = self.workdir / "wiki" / "data" / "sources" / module_subdir
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{stem}.md"

        def grow():
            path.write_text("a")
            for _ in range(5):
                time.sleep(0.4)
                with open(path, "a") as f:
                    f.write("b" * 100)
        threading.Thread(target=grow, daemon=True).start()
        v = self.verify_source(n=5, original_n=5,
                                module_subdir=module_subdir, stem=stem)
        self.assertEqual(v.get("verified"), "ok", v)
        self.assertGreater(path.stat().st_size, 100)

    # 7. K1 SRC 7 exact-path reproduction.
    def test_7_k1_src7_path_reproduction(self):
        module_subdir = "Психолог-консультант/001 Глубинная психология и психодиагностика в консультировании"
        stem = "004 №2. Психодинамический подход в психотерапии"
        self._put_source(module_subdir, stem, body="x" * 20000)
        v = self.verify_source(n=7, original_n=4,
                                module_subdir=module_subdir, stem=stem)
        self.assertEqual(v.get("verified"), "ok",
                         f"K1 SRC 7 exact path should grade ok on host; got {v}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
