"""Fixture: OpenAI-compatible HTTP shim that routes completions to Claude
(this conversation) via file-handoff.

Purpose: validate the reward-bench harness end-to-end without burning GPU
time or interrupting the active NVFP4 throughput sweep. OpenHands sees a
normal `/v1/chat/completions` endpoint; under the hood, each request is
serialised to disk, the human-in-the-loop (Claude) reads it, writes a
response file, and the shim returns it.

Usage:
    python claude_shim.py --root /tmp/rb-shim --port 8001

Then point OpenHands at:
    OPENAI_API_BASE=http://localhost:8001/v1
    OPENAI_API_KEY=fixture
    LLM_MODEL=claude-fixture

Per request, the shim:
    1. Writes the incoming chat-completion request to:
         {root}/prompts/turn-{NNN}.json
    2. Polls for {root}/responses/turn-{NNN}.json (timeout configurable)
    3. Returns the response in OpenAI-compatible format
    4. If timeout exceeds, returns 504

Claude (the human-in-the-loop) reads prompts/, writes responses/.

Non-streaming only — keeps the protocol trivial. Streaming can be added
later if OpenHands insists on it (it generally accepts non-streaming too).
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


class ShimState:
    def __init__(self, root: Path, poll_interval: float, timeout_sec: float):
        self.root = root
        self.prompts_dir = root / "prompts"
        self.responses_dir = root / "responses"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self.poll_interval = poll_interval
        self.timeout_sec = timeout_sec
        self.turn_counter = self._init_counter()

    def _init_counter(self) -> int:
        # Resume turn numbering across restarts
        existing = sorted(self.prompts_dir.glob("turn-*.json"))
        if not existing:
            return 0
        last = existing[-1].stem  # "turn-042"
        return int(last.split("-")[1]) + 1


def _make_handler(state: ShimState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(f"[shim] {self.address_string()} - {fmt % args}", flush=True)

        def _send(self, status: int, body: dict):
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path == "/v1/models":
                self._send(200, {
                    "object": "list",
                    "data": [{
                        "id": "claude-fixture",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "claude-shim",
                    }],
                })
                return
            self._send(404, {"error": f"unknown route: {self.path}"})

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                self._send(404, {"error": f"unknown route: {self.path}"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception as e:
                self._send(400, {"error": f"bad json: {e}"})
                return

            turn = state.turn_counter
            state.turn_counter += 1
            turn_id = f"turn-{turn:04d}"
            prompt_path = state.prompts_dir / f"{turn_id}.json"
            response_path = state.responses_dir / f"{turn_id}.json"

            # Persist a human-readable + machine-readable form
            prompt_path.write_text(json.dumps({
                "turn_id": turn_id,
                "received_at": time.time(),
                "model": body.get("model"),
                "messages": body.get("messages", []),
                "temperature": body.get("temperature"),
                "max_tokens": body.get("max_tokens"),
                "tools": body.get("tools"),
                "raw_request": body,
            }, indent=2, ensure_ascii=False))

            # Also write a flat .md beside it for easier human reading
            md_path = state.prompts_dir / f"{turn_id}.md"
            md_lines = [f"# {turn_id}", "", f"Model requested: `{body.get('model')}`", ""]
            for m in body.get("messages", []):
                role = m.get("role", "?").upper()
                content = m.get("content", "")
                if isinstance(content, list):
                    content = "\n".join(
                        c.get("text", "") if isinstance(c, dict) else str(c)
                        for c in content
                    )
                md_lines.append(f"## {role}\n\n{content}\n")
            md_path.write_text("\n".join(md_lines))

            print(f"[shim] queued {turn_id}; awaiting {response_path}", flush=True)

            # Poll for response
            deadline = time.time() + state.timeout_sec
            while time.time() < deadline:
                if response_path.exists():
                    try:
                        resp = json.loads(response_path.read_text())
                        text = resp.get("content", resp) if isinstance(resp, dict) else resp
                        if isinstance(text, dict):
                            text = text.get("text", json.dumps(text))
                        oai_response = {
                            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                            "object": "chat.completion",
                            "created": int(time.time()),
                            "model": body.get("model", "claude-fixture"),
                            "choices": [{
                                "index": 0,
                                "message": {"role": "assistant", "content": text},
                                "finish_reason": "stop",
                            }],
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0,
                            },
                        }
                        self._send(200, oai_response)
                        print(f"[shim] returned {turn_id}", flush=True)
                        return
                    except Exception as e:
                        self._send(500, {"error": f"bad response file: {e}"})
                        return
                time.sleep(state.poll_interval)

            # Timeout
            self._send(504, {"error": f"shim timeout after {state.timeout_sec}s waiting for {response_path}"})
            print(f"[shim] TIMEOUT on {turn_id}", flush=True)

    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="dir for prompts/ + responses/")
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--bind", default="127.0.0.1")
    ap.add_argument("--poll-interval", type=float, default=2.0)
    ap.add_argument("--timeout-sec", type=float, default=3600.0)
    args = ap.parse_args()

    state = ShimState(Path(args.root).resolve(), args.poll_interval, args.timeout_sec)
    handler = _make_handler(state)
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    print(f"[shim] listening on http://{args.bind}:{args.port}")
    print(f"[shim] root: {state.root}")
    print(f"[shim] prompts: {state.prompts_dir}")
    print(f"[shim] responses: {state.responses_dir}")
    print(f"[shim] turn counter starts at: {state.turn_counter}")
    print(f"[shim] poll every {state.poll_interval}s; per-turn timeout {state.timeout_sec}s")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[shim] stopped")


if __name__ == "__main__":
    main()
