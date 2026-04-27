#!/usr/bin/env python3
"""
F1 microbench: measure L* — max body length where tool_call.arguments
JSON parses for a given model + parser config.

Usage:
  python3 run_microbench.py \
    --base-url https://inference.mikhailov.tech/v1 \
    --api-key  $VLLM_API_KEY \
    --model    qwen3.6-27b-fp8 \
    --out      /mnt/steam/forge/labs/kurpatov-wiki-bench/evals/microbench/$(date +%F)-F1-qwen3.6-27b-fp8.csv

Reads forge/.env if --base-url/--api-key/--model not given.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.error

# Minimal file_editor tool spec — same shape as OpenHands SDK uses.
FILE_EDITOR_TOOL = {
    "type": "function",
    "function": {
        "name": "file_editor",
        "description": (
            "Create, view, or edit a file. Use 'create' to create a new file "
            "with the given content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "enum": ["create", "view", "str_replace", "insert"]},
                "path": {"type": "string", "description": "Absolute file path"},
                "file_text": {"type": "string", "description": "File content (for 'create')"},
            },
            "required": ["command", "path"],
        },
    },
}

CYRILLIC_PARAGRAPH_TEMPLATE = (
    "## Раздел №{n}\n\n"
    "Это абзац номер {n}. Он содержит русскоязычный текст с различными\n"
    "символами кириллицы — буквы, знаки препинания, цифры (1234567890),\n"
    "кавычки «ёлочки» и \"лапки\", тире — и многоточия... Параграф\n"
    "повторяется детерминированно, чтобы байтовая длина была воспроизводимой.\n\n"
)

PROMPT = (
    "Создай файл /tmp/test.md с заданным содержимым, используя инструмент "
    "file_editor (command=\"create\").\n\n"
    "Содержимое:\n\n{body}"
)


def gen_body(target_bytes: int) -> str:
    """Generate Cyrillic markdown of approximately target_bytes UTF-8 bytes (±32)."""
    parts = ["# Заголовок документа\n\n"]
    n = 0
    while True:
        cur_bytes = sum(len(p.encode("utf-8")) for p in parts)
        para = CYRILLIC_PARAGRAPH_TEMPLATE.format(n=n)
        if cur_bytes + len(para.encode("utf-8")) >= target_bytes:
            # truncate this paragraph in bytes, then trim to a valid utf-8 boundary
            remaining = target_bytes - cur_bytes
            encoded = para.encode("utf-8")[:remaining]
            while encoded:
                try:
                    parts.append(encoded.decode("utf-8"))
                    break
                except UnicodeDecodeError:
                    encoded = encoded[:-1]
            break
        parts.append(para)
        n += 1
    return "".join(parts)


def http_post_json(url: str, headers: dict, payload: dict, timeout_s: int = 300):
    req = urllib.request.Request(
        url,
        method="POST",
        headers=headers,
        data=json.dumps(payload).encode("utf-8"),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return e.code, body


def run_trial(base_url: str, api_key: str, model: str, target_bytes: int, trial: int) -> dict:
    body = gen_body(target_bytes)
    actual_bytes = len(body.encode("utf-8"))
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT.format(body=body)}],
        "tools": [FILE_EDITOR_TOOL],
        "tool_choice": "auto",
        "temperature": 0,
        "max_tokens": 32768,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    t0 = time.time()
    status, text = http_post_json(f"{base_url.rstrip('/')}/chat/completions", headers, payload)
    latency = time.time() - t0

    base = {
        "L_target": target_bytes,
        "L_bytes": actual_bytes,
        "trial": trial,
        "body_hash": body_hash,
        "latency_s": round(latency, 2),
    }

    if status != 200:
        return {**base, "passed": 0, "stop_reason": "http_error",
                "args_len": "", "error": f"http_{status}: {text[:160]}"}

    try:
        data = json.loads(text)
    except Exception as e:
        return {**base, "passed": 0, "stop_reason": "resp_not_json",
                "args_len": "", "error": f"resp_decode: {e}"}

    choice = data.get("choices", [{}])[0]
    finish = choice.get("finish_reason", "?")
    msg = choice.get("message") or {}
    tool_calls = msg.get("tool_calls") or []

    if not tool_calls:
        # Maybe model emitted a refusal or free-text
        free_content = (msg.get("content") or "")[:80]
        return {**base, "passed": 0, "stop_reason": finish,
                "args_len": "", "error": f"no_tool_calls. content={free_content}"}

    tc = tool_calls[0]
    args_raw = tc.get("function", {}).get("arguments", "")
    args_len = len(args_raw.encode("utf-8")) if isinstance(args_raw, str) else 0

    if not isinstance(args_raw, str):
        return {**base, "passed": 0, "stop_reason": finish,
                "args_len": args_len, "error": f"args_not_str: {type(args_raw).__name__}"}

    try:
        args_obj = json.loads(args_raw)
    except json.JSONDecodeError as e:
        return {**base, "passed": 0, "stop_reason": finish,
                "args_len": args_len,
                "error": f"json_decode: {e.msg} at char {e.pos}"}

    # Schema-ish validation: required fields present, no extra crashing
    if not isinstance(args_obj, dict):
        return {**base, "passed": 0, "stop_reason": finish, "args_len": args_len,
                "error": "args_not_object"}
    if "command" not in args_obj or "path" not in args_obj:
        return {**base, "passed": 0, "stop_reason": finish, "args_len": args_len,
                "error": f"missing_required: keys={list(args_obj.keys())}"}

    # Optional: check that file_text contains some of our body bytes (model didn't summarise)
    file_text = args_obj.get("file_text", "")
    body_overlap = 0
    if isinstance(file_text, str):
        # how many bytes of our body the model echoed back
        body_overlap = len(file_text.encode("utf-8"))

    return {**base, "passed": 1, "stop_reason": finish, "args_len": args_len,
            "file_text_bytes": body_overlap, "error": ""}


def load_env(env_path: Path) -> dict:
    if not env_path.exists():
        return {}
    out = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--env", default=str(Path.home() / "forge" / ".env"))
    p.add_argument("--base-url")
    p.add_argument("--api-key")
    p.add_argument("--model")
    p.add_argument("--lengths", default="1024,2048,4096,8192,12288,16384,24576,32768,49152")
    p.add_argument("--trials", type=int, default=10)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    env = load_env(Path(args.env))
    base_url = args.base_url or env.get("INFERENCE_BASE_URL") or "https://inference.mikhailov.tech/v1"
    api_key = args.api_key or env.get("VLLM_API_KEY") or os.environ.get("VLLM_API_KEY")
    model = args.model or env.get("INFERENCE_SERVED_NAME") or "qwen3.6-27b-fp8"

    if not api_key:
        sys.exit("ERROR: VLLM_API_KEY not provided (--api-key or in .env)")

    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"

    lengths = [int(x) for x in args.lengths.split(",")]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "date_utc", "model", "L_target", "L_bytes", "trial",
        "passed", "stop_reason", "args_len", "file_text_bytes",
        "latency_s", "body_hash", "error",
    ]
    date_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"# microbench start {date_utc}")
    print(f"#   base_url={base_url}")
    print(f"#   model={model}")
    print(f"#   lengths={lengths}")
    print(f"#   trials={args.trials}")
    print(f"#   out={out_path}\n")

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()

        for L in lengths:
            print(f"=== L_target={L} bytes ===")
            for trial in range(args.trials):
                r = run_trial(base_url, api_key, model, L, trial)
                row = {"date_utc": date_utc, "model": model, **r}
                w.writerow(row)
                f.flush()
                err_short = (r.get("error") or "")[:60]
                print(f"  trial {trial}: pass={r['passed']} "
                      f"stop={r.get('stop_reason')} "
                      f"args_len={r.get('args_len')} "
                      f"file_text={r.get('file_text_bytes', '?')} "
                      f"lat={r.get('latency_s', 0):.1f}s "
                      f"{('err='+err_short) if err_short else ''}")
            print()

    print(f"\nDone. CSV: {out_path}")


if __name__ == "__main__":
    main()
