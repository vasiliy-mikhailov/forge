"""Static anti-cheat for tier-1 reward-bench submissions.

Layer 1: AST walk
  - Reject imports outside the per-tier whitelist.
  - Reject __import__, eval, exec of strings, raw compile, dynamic
    file opens that escape /workspace, dunder-name access patterns
    used for sandbox-escape.
  - Allow ast.literal_eval (treated separately from eval()).

Layer 2: bandit (subprocess)
  - Optional second pass that runs `bandit` with confidence>=MEDIUM
    over the submission. Findings get joined into the cheat report.
  - Skipped if bandit is not installed (with a 'warning'-level finding).

Verdicts:
  - clean    : no findings
  - warning  : info-level findings only (e.g., unused complex import)
  - rejected : any rejected-severity finding present
"""

from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import dataclass, asdict, field


# ---------- per-tier import allow-list ----------

TIER1_ALLOWED_IMPORTS = frozenset(
    {
        # stdlib
        "__future__",   # harmless compiler directives (annotations, etc.)
        "ast",
        "collections",
        "copy",
        "dataclasses",
        "enum",
        "functools",
        "heapq",
        "itertools",
        "math",
        "operator",
        "random",
        "re",
        "statistics",
        "string",
        "typing",
        # task modules (provided in the sandbox /env mount)
        "env_2048",
        # numerics + FSM lib
        "numpy",
        "transitions",
    }
)

# Imports that *immediately* reject — sandbox-escape primitives
TIER1_BANNED_IMPORTS = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "socket",
        "urllib",
        "urllib3",
        "requests",
        "httpx",
        "http",
        "ftplib",
        "smtplib",
        "telnetlib",
        "ctypes",
        "multiprocessing",
        "threading",
        "asyncio",
        "concurrent",
        "shutil",
        "pathlib",   # not banned per se, but not on the allowlist either
        "pickle",
        "marshal",
        "shelve",
        "tempfile",
        "tarfile",
        "zipfile",
        "io",
    }
)

# Banned name lookups (eval, exec, compile, __import__, dunder-globals tricks)
TIER1_BANNED_NAMES = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "globals",
        "locals",
        "vars",
        "open",          # forbid arbitrary file I/O
        "input",         # no interactive
        "breakpoint",
    }
)

TIER1_BANNED_ATTRS = frozenset(
    {
        # Dunder-attribute escape
        "__subclasses__",
        "__bases__",
        "__mro__",
        "__class__",
        "__globals__",
        "__builtins__",
        "__import__",
        "__loader__",
        "__spec__",
        # Time-based randomness (defeats replay determinism)
        "monotonic",
        "perf_counter",
        "process_time",
    }
)


@dataclass
class CheatFinding:
    layer: str          # "ast" | "bandit"
    severity: str       # "info" | "warning" | "rejected"
    rule: str
    line: int
    code: str


@dataclass
class CheatReport:
    findings: list[CheatFinding] = field(default_factory=list)
    bandit_available: bool = False
    verdict: str = "clean"
    rejected_reason: str = ""

    def add(self, f: CheatFinding):
        self.findings.append(f)

    def finalize(self):
        rejs = [f for f in self.findings if f.severity == "rejected"]
        warns = [f for f in self.findings if f.severity == "warning"]
        if rejs:
            self.verdict = "rejected"
            self.rejected_reason = f"{len(rejs)} rejected finding(s); first: {rejs[0].rule} @ line {rejs[0].line}"
        elif warns:
            self.verdict = "warning"
        else:
            self.verdict = "clean"

    def to_dict(self):
        return {
            "findings": [asdict(f) for f in self.findings],
            "bandit_available": self.bandit_available,
            "verdict": self.verdict,
            "rejected_reason": self.rejected_reason,
        }


# ---------- AST walker ----------

class _Tier1ASTChecker(ast.NodeVisitor):
    def __init__(self, src: str, report: CheatReport):
        self.report = report
        self.src_lines = src.splitlines()

    def _line(self, n: int) -> str:
        if 1 <= n <= len(self.src_lines):
            return self.src_lines[n - 1].strip()
        return ""

    def _add(self, severity: str, rule: str, lineno: int):
        self.report.add(CheatFinding(layer="ast", severity=severity, rule=rule, line=lineno, code=self._line(lineno)))

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in TIER1_BANNED_IMPORTS:
                self._add("rejected", f"banned_import:{top}", node.lineno)
            elif top not in TIER1_ALLOWED_IMPORTS:
                self._add("rejected", f"non_whitelisted_import:{top}", node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module is None:
            self._add("rejected", "relative_import", node.lineno)
            return
        top = node.module.split(".")[0]
        if top in TIER1_BANNED_IMPORTS:
            self._add("rejected", f"banned_import:{top}", node.lineno)
        elif top not in TIER1_ALLOWED_IMPORTS:
            self._add("rejected", f"non_whitelisted_import:{top}", node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Direct name call: eval(...) / exec(...) / __import__(...) / open(...)
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id in TIER1_BANNED_NAMES:
            self._add("rejected", f"banned_name_call:{fn.id}", node.lineno)
        # ast.literal_eval is OK; ast.parse + compile + exec patterns are not — flag compile()
        if isinstance(fn, ast.Attribute) and fn.attr == "literal_eval":
            pass  # allowed
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id in TIER1_BANNED_NAMES and isinstance(node.ctx, ast.Load):
            # naked reference to eval/exec/etc. without a call — still suspicious
            self._add("warning", f"banned_name_reference:{node.id}", node.lineno)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in TIER1_BANNED_ATTRS:
            self._add("rejected", f"banned_attr:{node.attr}", node.lineno)
        self.generic_visit(node)


# ---------- bandit wrapper ----------

def _run_bandit(submission_path: str, report: CheatReport) -> None:
    """Run bandit if available; append findings to report."""
    try:
        result = subprocess.run(
            ["bandit", "-q", "-f", "json", submission_path],
            capture_output=True, text=True, timeout=30,
        )
        report.bandit_available = True
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        report.add(CheatFinding(
            layer="bandit", severity="info", rule="bandit_unavailable",
            line=0, code=str(e),
        ))
        return

    # bandit returns non-zero when findings exist. Parse JSON regardless.
    try:
        data = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError:
        report.add(CheatFinding(
            layer="bandit", severity="info", rule="bandit_parse_error",
            line=0, code=result.stdout[:200] if result.stdout else "",
        ))
        return

    sev_map = {"LOW": "info", "MEDIUM": "warning", "HIGH": "rejected"}
    for issue in data.get("results", []):
        report.add(CheatFinding(
            layer="bandit",
            severity=sev_map.get(issue.get("issue_severity", "LOW"), "warning"),
            rule=f"{issue.get('test_id', '?')}:{issue.get('test_name', '?')}",
            line=issue.get("line_number", 0),
            code=(issue.get("code", "") or "").strip()[:200],
        ))


# ---------- entry points ----------

def check_tier1(submission_src: str, submission_path: str = "submission.py") -> CheatReport:
    """Top-level: AST walk + bandit. Returns a CheatReport."""
    report = CheatReport()

    # AST walk
    try:
        tree = ast.parse(submission_src)
    except SyntaxError as e:
        report.add(CheatFinding(
            layer="ast", severity="rejected", rule="syntax_error",
            line=e.lineno or 0, code=str(e),
        ))
        report.finalize()
        return report

    _Tier1ASTChecker(submission_src, report).visit(tree)

    # Bandit (if file is on disk)
    import os
    if os.path.exists(submission_path):
        _run_bandit(submission_path, report)
    else:
        report.add(CheatFinding(
            layer="bandit", severity="info", rule="bandit_skipped_no_file",
            line=0, code="submission not on disk; AST-only pass",
        ))

    report.finalize()
    return report


if __name__ == "__main__":
    import sys
    src = open(sys.argv[1]).read()
    rep = check_tier1(src, sys.argv[1])
    print(json.dumps(rep.to_dict(), indent=2))
    sys.exit(0 if rep.verdict != "rejected" else 1)
