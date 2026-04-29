"""INTEGRATION tests for `verify_source` — production-faithful per ADR 0010.

Production call path:
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
  - Process boundary: SAME container image
    (kurpatov-wiki-bench:1.17.0-d8-cal) as K1.
  - Write/read mechanism: SAME FileEditor.__call__("create") that
    the agent invokes. NOT Path.write_text().
  - Filesystem stack: SAME /workspace bind-mount style as K1
    (host /tmp -> container /workspace).
  - Python interpreter: SAME 3.12 + same OpenHands SDK version
    baked into the bench image.
  - Locale: container's default; production sets LC_ALL=C.UTF-8 in
    Dockerfile; we inherit.
  - Write timing: simulates the agent's "write file then verify"
    pattern. Three timing variants — write-before-verify (no race),
    write-then-immediately-verify, write-via-thread-during-verify.
Skipped: the LLM driving the agent (irrelevant for verify_source's
  poll); the Conversation/event-loop machinery (orthogonal).

Run via run_integration_tests.sh which spawns this file inside the
bench image with /tmp/k1-pilot bind-mounted.
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

ORCH = Path(os.environ.get("ORCH_DIR", "/opt/forge"))


def _extract_function(name: str) -> str:
    src = (ORCH / "run-d8-pilot.py").read_text()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return "\n".join(src.splitlines()[node.lineno - 1:node.end_lineno])
    raise RuntimeError(f"function {name!r} not in run-d8-pilot.py")


def _load_verify_source(workdir: Path, bench_grade_path: str):
    ns = {
        "__name__": "verify_source_integration",
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


class VerifySourceIntegrationTests(unittest.TestCase):
    """Integration tests using the actual FileEditor inside the bench
    container."""

    def setUp(self):
        # Workspace bind-mount style: assume /workspace exists and is writable.
        # Use a unique subdir per test so concurrent runs don't collide.
        import tempfile
        self.workdir = Path(tempfile.mkdtemp(prefix="verify_int_", dir="/workspace"))
        (self.workdir / "wiki" / "data" / "sources").mkdir(parents=True)
        self.stub = self.workdir / "stub_bench_grade.py"
        self.stub.write_text(
            "import json, sys\n"
            "print(json.dumps({'verified': 'ok', 'violations': []}))\n"
        )
        self.verify_source = _load_verify_source(self.workdir, str(self.stub))

        # Initialize the SAME FileEditor the agent uses.
        from openhands.tools.file_editor.editor import FileEditor
        self.editor = FileEditor(workspace_root=str(self.workdir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.workdir, ignore_errors=True)

    def _put_via_file_editor(self, module_subdir: str, stem: str, body: str = "x\n"):
        """Write the source.md exactly the way the agent does:
        FileEditor.__call__(command="create", path=..., file_text=...)."""
        d = self.workdir / "wiki" / "data" / "sources" / module_subdir
        d.mkdir(parents=True, exist_ok=True)
        path = str(d / f"{stem}.md")
        # This is the SAME call the OpenHands agent issues for a 'create' op.
        self.editor(command="create", path=path, file_text=body)
        return Path(path)

    # 1. ASCII path, write via FileEditor, immediately verify.
    def test_1_ascii_via_file_editor(self):
        self._put_via_file_editor("course/module-a", "001 source")
        v = self.verify_source(n=1, original_n=1,
                                module_subdir="course/module-a",
                                stem="001 source")
        self.assertEqual(v.get("verified"), "ok",
                         f"FileEditor write -> verify: expected ok, got {v}")

    # 2. Cyrillic path via FileEditor.
    def test_2_cyrillic_via_file_editor(self):
        module_subdir = "Психолог-консультант/000 Путеводитель по программе"
        stem = "000 Знакомство с программой «Психолог-консультант»"
        self._put_via_file_editor(module_subdir, stem)
        v = self.verify_source(n=0, original_n=0,
                                module_subdir=module_subdir, stem=stem)
        self.assertEqual(v.get("verified"), "ok", v)

    # 3. K1 SRC 7 EXACT path reproduction via FileEditor.
    def test_3_k1_src7_via_file_editor(self):
        module_subdir = "Психолог-консультант/001 Глубинная психология и психодиагностика в консультировании"
        stem = "004 №2. Психодинамический подход в психотерапии"
        self._put_via_file_editor(module_subdir, stem, body="x" * 20000)
        v = self.verify_source(n=7, original_n=4,
                                module_subdir=module_subdir, stem=stem)
        self.assertEqual(v.get("verified"), "ok",
                         f"K1 SRC 7 via FileEditor: expected ok, got {v}")

    # 4. File written via FileEditor in a thread that runs DURING verify_source.
    #    Most production-faithful for the K1 race scenario.
    def test_4_file_editor_write_during_poll(self):
        module_subdir = "course/module"
        stem = "004 deferred"
        d = self.workdir / "wiki" / "data" / "sources" / module_subdir
        d.mkdir(parents=True, exist_ok=True)
        path_str = str(d / f"{stem}.md")

        def deferred_write():
            time.sleep(2.0)
            self.editor(command="create", path=path_str, file_text="x" * 5000)

        threading.Thread(target=deferred_write, daemon=True).start()
        v = self.verify_source(n=4, original_n=4,
                                module_subdir=module_subdir, stem=stem)
        self.assertEqual(v.get("verified"), "ok",
                         f"FileEditor deferred write during poll: expected ok, got {v}")

    # 5. Negative test — file never written, verify must fail.
    def test_5_no_write_fails_within_short_deadline(self):
        v = self.verify_source(n=5, original_n=5,
                                module_subdir="course/module",
                                stem="005 missing",
                                deadline_secs=3.0)
        self.assertEqual(v.get("verified"), "fail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
