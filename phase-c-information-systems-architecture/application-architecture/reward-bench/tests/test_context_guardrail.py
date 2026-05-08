#!/usr/bin/env python3
"""Tests for the agent_loop context-budget guardrail.

This is the regression test for the May-08 incident where the campaign
ran with --condenser-trigger-tokens=80000 against a model with
max_model_len=65536; vLLM rejected requests beyond input=53248 with
HTTP 400, and trials wasted hundreds of turns on retries because the
watchdog (set to 80K) never fired.

The guardrail being tested:
  At startup, query the candidate's /v1/models for max_model_len.
  Compute max_safe_input = max_model_len - max_tokens (default 12288).
  If condenser is enabled and trigger_tokens >= max_safe_input, refuse
  to start with a clear error message. Same check for the no-condenser
  fallback (context_budget_tokens >= max_safe_input).

Run:
    python3 test_context_guardrail.py
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler

AGENT_LOOP = "/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/reward-bench/bin/agent_loop.py"


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def make_mock_vllm(port: int, max_model_len: int):
    """Spawn a tiny stdlib HTTP server that mimics vLLM's /v1/models."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a, **kw): pass  # quiet

        def do_GET(self):
            if self.path.startswith("/v1/models"):
                payload = {
                    "object": "list",
                    "data": [{
                        "id": "mock-candidate",
                        "object": "model",
                        "max_model_len": max_model_len,
                        "owned_by": "mock",
                    }]
                }
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404); self.end_headers()

        def do_POST(self):
            self.send_response(503); self.end_headers()

    httpd = HTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def run_agent_loop(extra_args: list[str], shim_url: str, expect_rc: int | None = None,
                   timeout: int = 30) -> tuple[int, str, str]:
    """Run agent_loop subprocess. Returns (rc, stdout, stderr)."""
    workspace = "/tmp/test_workspace"
    os.makedirs(workspace, exist_ok=True)
    cmd = [
        sys.executable, "-u", AGENT_LOOP,
        "--shim", shim_url, "--api-key", "fixture", "--model", "mock-candidate",
        "--workspace", workspace,
        "--tasks-dir", "/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/reward-bench/tasks",
        "--env-dir", "/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/reward-bench/tasks/2048",
        "--max-iters", "1",
    ] + extra_args
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


class TestContextGuardrail(unittest.TestCase):
    """Each test spins up a fresh mock vLLM advertising a specific max_model_len."""

    def test_unsafe_condenser_trigger_is_rejected(self):
        """trigger >= max_safe_input must abort with a clear error before turn 1."""
        max_len = 65536
        port = free_port()
        srv = make_mock_vllm(port, max_len)
        try:
            shim = f"http://127.0.0.1:{port}/v1"
            rc, out, err = run_agent_loop(
                extra_args=[
                    "--condenser-shim", shim,
                    "--condenser-model", "mock-condenser",
                    "--condenser-trigger-tokens", "80000",   # >= 65536-12288=53248
                ],
                shim_url=shim,
            )
            combined = (out + "\n" + err).lower()
            # Should refuse to start. Specifically should NOT enter the loop
            # (which would manifest as a `=== turn 1 ===` heading in stdout).
            self.assertNotIn("=== turn 1 ===", out,
                             f"agent_loop entered the loop with unsafe config:\n{out[-2000:]}")
            self.assertNotEqual(rc, 0, "agent_loop should fail-fast with non-zero rc")
            self.assertTrue(
                any(k in combined for k in (
                    "max_safe_input", "condenser-trigger-tokens", "max_model_len",
                    "context-budget", "guardrail", "would exceed",
                )),
                f"error must explain the safety issue. got:\nstdout={out[-1000:]}\nstderr={err[-1000:]}"
            )
        finally:
            srv.shutdown()

    def test_safe_condenser_trigger_allowed(self):
        """trigger comfortably below max_safe_input must NOT be rejected by the guardrail.

        We point the condenser at a non-existent shim so agent_loop will
        get past the guardrail then fail later — that's fine, we only
        care that the guardrail itself doesn't fire.
        """
        max_len = 65536
        port = free_port()
        srv = make_mock_vllm(port, max_len)
        try:
            shim = f"http://127.0.0.1:{port}/v1"
            rc, out, err = run_agent_loop(
                extra_args=[
                    "--condenser-shim", shim,
                    "--condenser-model", "mock-condenser",
                    "--condenser-trigger-tokens", "40000",   # well below 53248
                ],
                shim_url=shim,
            )
            combined = (out + "\n" + err).lower()
            # The guardrail's *abort* messages should NOT appear. Note: the
            # success line also contains "max_safe_input", so we only check
            # for the abort marker "would exceed" here.
            self.assertNotIn(
                "would exceed", combined,
                f"safe config should pass guardrail. got:\nstdout={out[-800:]}\nstderr={err[-800:]}"
            )
        finally:
            srv.shutdown()

    def test_no_condenser_with_unsafe_context_budget_is_rejected(self):
        """Without condenser, --context-budget-tokens must also be < max_safe_input."""
        max_len = 65536
        port = free_port()
        srv = make_mock_vllm(port, max_len)
        try:
            shim = f"http://127.0.0.1:{port}/v1"
            rc, out, err = run_agent_loop(
                extra_args=[
                    "--context-budget-tokens", "200000",  # WAY above 53248
                ],
                shim_url=shim,
            )
            combined = (out + "\n" + err).lower()
            self.assertNotIn("=== turn 1 ===", out)
            self.assertNotEqual(rc, 0)
            self.assertTrue(
                any(k in combined for k in (
                    "max_safe_input", "context-budget", "max_model_len", "would exceed",
                )),
                f"error must explain the safety issue. got:\nstdout={out[-1000:]}\nstderr={err[-1000:]}"
            )
        finally:
            srv.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
