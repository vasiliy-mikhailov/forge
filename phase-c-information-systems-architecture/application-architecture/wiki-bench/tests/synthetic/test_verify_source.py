"""Synth UNIT tests for `verify_source` — written FIRST per TDD.

Production call path (per ADR 0010):
  orchestrator main loop
    -> Conversation.run() (OpenHands SDK)
       -> Agent.execute_tool("file_editor", command="create", ...)
          -> openhands.tools.file_editor.FileEditor.__call__()
             -> FileEditor.write_file()
                -> open()/write()/close() to /workspace/...
       -> Agent.execute_tool("finish")
    <- conv.run() returns
  orchestrator calls verify_source()
    -> Path(target).stat() in this process

Test fidelity (per ADR 0010):
  - Process boundary: HOST python, NOT inside the bench container.
  - Write/read mechanism: writes via Path.write_text() — DIFFERENT
    from production's FileEditor.__call__("create"). This is the
    chief abstraction these tests do.
  - Filesystem: HOST tempfs (no bind mount to /workspace).
  - Python: HOST 3.x — may differ from container's 3.12.
  - Locale: HOST default.
  - Write timing: file is put on disk via a thread that simulates
    the agent's deferred write.

These tests prove: `verify_source`'s poll logic is correct under
direct-host file writes. They do NOT prove: that production's
FileEditor write path produces a file that `verify_source`'s
poll detects within the deadline.

For the integration tests that DO exercise FileEditor inside the
bench container, see `test_verify_source_integration.py` (run
via `run_integration_tests.sh`).
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


def _extract_function(name: str) -> str:
    src = (ORCH / "run-d8-pilot.py").read_text()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return "\n".join(src.splitlines()[node.lineno - 1:node.end_lineno])
    raise RuntimeError(f"function {name!r} not in run-d8-pilot.py")


def _load_verify_source(workdir: Path, bench_grade_path: str):
    ns = {
        "__name__": "verify_source_test_module",
        "WORKDIR": workdir,
        "BENCH_GRADE": bench_grade_path,
        "Path": Path,
        "subprocess": __import__("subprocess"),
        "json": json,
        "time": time,
    }
    code = _extract_function("verify_source")
    exec(compile(code, str(ORCH / "run-d8-pilot.py"), "exec"), ns)
    return ns["verify_source"]


class VerifySourceUnitTests(unittest.TestCase):
    """UNIT tests of verify_source's polling logic. Direct-host writes
    only — not faithful to production's FileEditor write path.
    Integration tests live in test_verify_source_integration.py."""

    def setUp(self):
        import tempfile
        self.tmpdir = Path(tempfile.mkdtemp(prefix="verify_test_"))
        self.workdir = self.tmpdir / "workspace"
        (self.workdir / "wiki" / "data" / "sources").mkdir(parents=True)
        self.stub = self.tmpdir / "stub_bench_grade.py"
        self.stub.write_text(
            "import json, sys\n"
            "print(json.dumps({'verified': 'ok', 'violations': []}))\n"
        )
        self.verify_source = _load_verify_source(self.workdir, str(self.stub))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _put_source(self, module_subdir: str, stem: str, body: str = "x\n"):
        d = self.workdir / "wiki" / "data" / "sources" / module_subdir
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{stem}.md").write_text(body, encoding="utf-8")

    def test_1_ascii_existing_file(self):
        self._put_source("course/module-a", "001 source")
        v = self.verify_source(n=1, original_n=1,
                                module_subdir="course/module-a",
                                stem="001 source")
        self.assertEqual(v.get("verified"), "ok", v)

    def test_2_cyrillic_existing_file(self):
        module_subdir = "Психолог-консультант/000 Путеводитель по программе"
        stem = "000 Знакомство с программой «Психолог-консультант»"
        self._put_source(module_subdir, stem)
        v = self.verify_source(n=0, original_n=0,
                                module_subdir=module_subdir, stem=stem)
        self.assertEqual(v.get("verified"), "ok", v)

    def test_3_file_appears_after_1s(self):
        threading.Thread(
            target=lambda: (time.sleep(1.0), self._put_source("c/m", "002 deferred")),
            daemon=True,
        ).start()
        t0 = time.monotonic()
        v = self.verify_source(n=2, original_n=2,
                                module_subdir="c/m", stem="002 deferred")
        self.assertEqual(v.get("verified"), "ok", v)
        self.assertLess(time.monotonic() - t0, 5.0)

    def test_5_file_never_appears(self):
        v = self.verify_source(n=4, original_n=4,
                                module_subdir="c/m", stem="004 missing",
                                deadline_secs=3.0)
        self.assertEqual(v.get("verified"), "fail")
        joined = " ".join(str(x) for x in (v.get("violations") or []))
        self.assertIn("did not appear", joined)

    def test_6_file_size_growing(self):
        d = self.workdir / "wiki" / "data" / "sources" / "c/m"
        d.mkdir(parents=True, exist_ok=True)
        path = d / "005 growing.md"

        def grow():
            path.write_text("a")
            for _ in range(5):
                time.sleep(0.4)
                with open(path, "a") as f:
                    f.write("b" * 100)
        threading.Thread(target=grow, daemon=True).start()
        v = self.verify_source(n=5, original_n=5,
                                module_subdir="c/m", stem="005 growing")
        self.assertEqual(v.get("verified"), "ok", v)
        self.assertGreater(path.stat().st_size, 100)

    def test_7_k1_src7_path_reproduction(self):
        module_subdir = "Психолог-консультант/001 Глубинная психология и психодиагностика в консультировании"
        stem = "004 №2. Психодинамический подход в психотерапии"
        self._put_source(module_subdir, stem, body="x" * 20000)
        v = self.verify_source(n=7, original_n=4,
                                module_subdir=module_subdir, stem=stem)
        self.assertEqual(v.get("verified"), "ok", v)


if __name__ == "__main__":
    unittest.main(verbosity=2)
