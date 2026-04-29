"""E2E tests for `verify_source` — REAL OpenHands agent loop with REAL LLM.

Production call path (per ADR 0010):
  orchestrator main loop
    -> conv = Conversation(agent=Agent(llm=LLM(...), tools=[file_editor, finish]),
                            workspace=...)
    -> conv.send_message(...)
    -> conv.run()             [agent loop: LLM tokens -> tool calls -> observations -> ...]
       -> Agent.execute_tool("file_editor", command="create", ...)
          -> FileEditor.__call__()
             -> FileEditor.write_file()
                -> open()/write()/close() to /workspace/...
       -> Agent.execute_tool("finish")
    <- conv.run() returns
  orchestrator calls verify_source()
    -> Path(target).stat() in this process

Test fidelity (per ADR 0010):
  - Process boundary: SAME container image (kurpatov-wiki-bench:1.17.0-d8-cal).
  - Write/read mechanism: SAME FileEditor invocation, but driven BY THE LLM via
    the OpenHands SDK Agent loop. NOT direct FileEditor() calls; not Path.write_text.
  - Filesystem: SAME /workspace bind-mount.
  - Python: SAME 3.12 + same SDK.
  - Locale: container default + LC_ALL=C.UTF-8 in run script.
  - Write timing: agent finishes the conversation, conv.run() returns, then
    verify_source is called immediately. EXACTLY the production K1 sequence.
  - Conversation state: a real Conversation with real events.
  - LLM: real vLLM at INFERENCE_BASE_URL (Qwen3.6-27B-FP8 or whatever is active).
Skipped: nothing relevant to the verify_source race. This is the highest-fidelity
  test we can write at our layer.

Test runtime: ~60-120 s per test (real LLM round-trips).

Run via run_e2e_tests.sh which spawns this file inside the bench image.
"""
from __future__ import annotations
import ast
import json
import os
import sys
import time
import unittest
import uuid
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
        "__name__": "verify_source_e2e",
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


def _make_agent_and_conv(workspace: Path):
    """Build a minimal OpenHands Agent + Conversation pointed at the local
    vLLM endpoint, with file_editor and finish tools."""
    from openhands.sdk import LLM, Agent, Conversation, Tool
    from openhands.sdk.tool import register_tool
    from openhands.tools.file_editor import FileEditorTool
    from pydantic import SecretStr

    base_url = os.environ.get("LLM_BASE_URL", "https://inference.mikhailov.tech/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8")

    # Register the FileEditorTool definition so Agent can resolve Tool(name=...).
    # Mirrors how the orchestrator's setup_agents() does it. Idempotent: re-
    # registering the same name with the same class is fine across tests.
    try:
        register_tool("FileEditorTool", FileEditorTool)
    except Exception:
        # Already registered (e.g., second test in the same process) — ignore.
        pass

    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
        usage_id="e2e-test",
    )
    agent = Agent(
        llm=llm,
        tools=[Tool(name="FileEditorTool")],
    )
    conv = Conversation(
        agent=agent,
        workspace=str(workspace),
        max_iteration_per_run=20,
    )
    return conv


class VerifySourceE2ETests(unittest.TestCase):
    """E2E tests using real Agent + real LLM + real file_editor."""

    @classmethod
    def setUpClass(cls):
        # Required env vars present?
        if not os.environ.get("LLM_API_KEY"):
            raise unittest.SkipTest("LLM_API_KEY not set; skipping e2e tests")

    def setUp(self):
        import tempfile
        # Use a unique subdir per test under /workspace.
        self.workdir = Path(tempfile.mkdtemp(prefix="verify_e2e_", dir="/workspace"))
        (self.workdir / "wiki" / "data" / "sources").mkdir(parents=True)
        self.stub = self.workdir / "stub_bench_grade.py"
        self.stub.write_text(
            "import json, sys\n"
            "print(json.dumps({'verified': 'ok', 'violations': []}))\n"
        )
        self.verify_source = _load_verify_source(self.workdir, str(self.stub))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.workdir, ignore_errors=True)

    # 1. Agent writes a single ASCII-named file and finishes.
    #    verify_source should find it immediately.
    def test_1_agent_writes_then_finish(self):
        from openhands.sdk import Message, TextContent
        module_subdir = "course/module-a"
        stem = "001 hello"
        target_rel = f"wiki/data/sources/{module_subdir}/{stem}.md"
        target_abs = str(self.workdir / target_rel)

        # Production parity: orchestrator pre-creates the module subdir before
        # invoking the agent. FileEditor's create command does NOT mkdir -p.
        (self.workdir / "wiki" / "data" / "sources" / module_subdir).mkdir(
            parents=True, exist_ok=True
        )

        conv = _make_agent_and_conv(self.workdir)
        conv.send_message(Message(
            role="user",
            content=[TextContent(text=(
                f"Use file_editor with command='create' to create the file at "
                f"absolute path {target_abs!r} with the content "
                f"'frontmatter\\n---\\nbody of source 001.\\n'. "
                f"Then call finish."
            ))],
        ))
        t0 = time.monotonic()
        conv.run()
        t_run = time.monotonic() - t0
        print(f"  conv.run() took {t_run:.1f}s", flush=True)

        # Immediately call verify_source — exactly the production sequence.
        v = self.verify_source(n=1, original_n=1,
                                module_subdir=module_subdir,
                                stem=stem,
                                deadline_secs=15.0)
        self.assertEqual(v.get("verified"), "ok",
                         f"E2E: agent wrote file via file_editor, verify expected ok, got {v}")

    # 2. K1 SRC 0 EXACT path — Cyrillic + curly «» — driven by the real LLM.
    def test_2_k1_src0_path_e2e(self):
        from openhands.sdk import Message, TextContent
        module_subdir = "Психолог-консультант/000 Путеводитель по программе"
        stem = "000 Знакомство с программой «Психолог-консультант»"
        target_rel = f"wiki/data/sources/{module_subdir}/{stem}.md"
        target_abs = str(self.workdir / target_rel)

        # Production parity: orchestrator pre-creates the module subdir.
        (self.workdir / "wiki" / "data" / "sources" / module_subdir).mkdir(
            parents=True, exist_ok=True
        )

        conv = _make_agent_and_conv(self.workdir)
        conv.send_message(Message(
            role="user",
            content=[TextContent(text=(
                f"Use file_editor with command='create' to create the file at "
                f"absolute path {target_abs!r} with content "
                f"'frontmatter\\n---\\n# Test source 0\\n\\n## TL;DR\\nminimal body.\\n'. "
                f"Then call finish."
            ))],
        ))
        conv.run()

        v = self.verify_source(n=0, original_n=0,
                                module_subdir=module_subdir,
                                stem=stem,
                                deadline_secs=15.0)
        self.assertEqual(v.get("verified"), "ok",
                         f"K1 SRC 0 path e2e: expected ok, got {v}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
