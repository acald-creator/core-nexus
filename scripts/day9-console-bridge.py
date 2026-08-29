#!/usr/bin/env python3
"""Day 9 bridge: temporary mock Ollama + athena-agents HTTP shim for Console Agent Feed.

Host OPAR writes ground-truth JSONL. The Gateway expects athena-agents on :8080
with /sessions and /events. That HTTP surface does not exist yet.

This bridge:
  - Serves a canned Ollama-compatible planner on :11435 so the orchestrator can run
  - Tails ATHENA_GT_OUTPUT and streams OPAR-shaped SSE on :8080 for the Console

Stdlib only. Not production. Start only via:
  NEXUS_ENABLE_DAY9_BRIDGE=1 ./scripts/start-day9-dev-stack.sh
Replace with a real athena-agents event source when available.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Queue
from typing import Any

GT_PATH = Path(os.environ.get("ATHENA_GT_OUTPUT", "/tmp/juice-shop-day9-gt.jsonl"))
SESSION_ID = os.environ.get("ATHENA_DAY9_SESSION", f"day9-{uuid.uuid4().hex[:8]}")
TARGET = "localhost"

# http-request only — host tool registry points port-scanner at a missing binary.
PLAN_CYCLE = [
    {
        "tool_id": "http-request",
        "arguments": {"url": "http://localhost:3001/"},
        "technique": "T1190",
        "rationale": "Day9 bridge: GET the Juice Shop home page.",
    },
    {
        "tool_id": "http-request",
        "arguments": {"url": "http://localhost:3001/rest/products/search?q=qwert%27)"},
        "technique": "T1190",
        "rationale": "Day9 bridge: probe a known Juice Shop SQLi search shape.",
    },
    {
        "tool_id": "http-request",
        "arguments": {"url": "http://localhost:3001/api/Users"},
        "technique": "T1082",
        "rationale": "Day9 bridge: touch the Users API surface.",
    },
    {
        "tool_id": "http-request",
        "arguments": {"url": "http://localhost:3001/rest/user/whoami"},
        "technique": "T1082",
        "rationale": "Day9 bridge: whoami without a session.",
    },
    {
        "tool_id": "http-request",
        "arguments": {"url": "http://localhost:3001/#/login"},
        "technique": "T1078",
        "rationale": "Day9 bridge: hit the login route.",
    },
    {
        "tool_id": "http-request",
        "arguments": {"url": "http://localhost:3001/ftp"},
        "technique": "T1083",
        "rationale": "Day9 bridge: probe the exposed /ftp directory.",
    },
]

_plan_idx = 0
_plan_lock = threading.Lock()
_subscribers: list[Queue] = []
_sub_lock = threading.Lock()
_session_started = time.time()
_event_count = 0
_event_lock = threading.Lock()


def gt_to_opar(record: dict[str, Any]) -> dict[str, Any]:
    global _event_count
    with _event_lock:
        _event_count += 1
        n = _event_count
    label = record.get("label", "")
    outcome = "pending" if label == "needs_review" else "success"
    return {
        "id": f"{record.get('run_id', SESSION_ID)}-{n}",
        "timestamp": record.get("timestamp")
        or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sessionId": record.get("run_id") or SESSION_ID,
        "phase": "act",
        "target": record.get("target") or TARGET,
        "toolName": record.get("payload_family") or "opar",
        "outcomeStatus": outcome,
        "payload": {
            "technique": record.get("technique"),
            "expected_result": record.get("expected_result"),
            "label": label,
            "scenario_id": record.get("scenario_id"),
            "source": "day9-gt-bridge",
        },
    }


def broadcast(event: dict[str, Any]) -> None:
    with _sub_lock:
        subs = list(_subscribers)
    for q in subs:
        try:
            q.put_nowait(event)
        except Exception:
            pass


def tail_gt() -> None:
    """Follow GT JSONL; reopen on truncate or inode replace (rm + recreate)."""
    GT_PATH.parent.mkdir(parents=True, exist_ok=True)
    GT_PATH.touch(exist_ok=True)
    seen_inode: int | None = None
    offset = 0
    while True:
        try:
            st = GT_PATH.stat()
        except FileNotFoundError:
            GT_PATH.touch(exist_ok=True)
            time.sleep(0.2)
            continue
        if seen_inode != st.st_ino:
            seen_inode = st.st_ino
            offset = 0
        with GT_PATH.open("r", encoding="utf-8") as fh:
            fh.seek(offset)
            while True:
                line = fh.readline()
                if not line:
                    offset = fh.tell()
                    try:
                        st2 = GT_PATH.stat()
                    except FileNotFoundError:
                        break
                    if st2.st_ino != seen_inode or st2.st_size < offset:
                        break
                    time.sleep(0.15)
                    continue
                offset = fh.tell()
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                broadcast(gt_to_opar(record))
        time.sleep(0.1)


class OllamaHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[ollama-mock] {fmt % args}", flush=True)

    def do_GET(self) -> None:
        if self.path.startswith("/api/tags"):
            body = json.dumps({"models": [{"name": "day9-bridge", "model": "day9-bridge"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        global _plan_idx
        if self.path.startswith("/api/generate"):
            length = int(self.headers.get("Content-Length", "0"))
            if length:
                self.rfile.read(length)
            with _plan_lock:
                plan = PLAN_CYCLE[_plan_idx % len(PLAN_CYCLE)]
                _plan_idx += 1
            body = json.dumps(
                {"response": json.dumps(plan), "done": True, "model": "day9-bridge"}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)


class AthenaHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[athena-shim] {fmt % args}", flush=True)

    def do_GET(self) -> None:
        if self.path.startswith("/sessions"):
            with _event_lock:
                count = _event_count
            body = json.dumps(
                [
                    {
                        "id": SESSION_ID,
                        "target": TARGET,
                        "status": "running",
                        "started_at": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(_session_started)
                        ),
                        "event_count": count,
                        "gt_path": str(GT_PATH),
                    }
                ]
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith("/approvals"):
            body = b"[]"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith("/events"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            q: Queue = Queue(maxsize=200)
            with _sub_lock:
                _subscribers.append(q)
            hello = {
                "id": f"{SESSION_ID}-hello",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sessionId": SESSION_ID,
                "phase": "observe",
                "target": TARGET,
                "outcomeStatus": "pending",
                "payload": {"message": "day9 bridge connected", "gt_path": str(GT_PATH)},
            }
            try:
                self.wfile.write(f"data: {json.dumps(hello)}\n\n".encode())
                self.wfile.flush()
                while True:
                    try:
                        event = q.get(timeout=10.0)
                        self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
                        self.wfile.flush()
                    except Empty:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with _sub_lock:
                    if q in _subscribers:
                        _subscribers.remove(q)
            return

        self.send_error(404)


def main() -> None:
    threading.Thread(target=tail_gt, name="gt-tail", daemon=True).start()
    ollama = ThreadingHTTPServer(("127.0.0.1", 11435), OllamaHandler)
    athena = ThreadingHTTPServer(("127.0.0.1", 8080), AthenaHandler)
    threading.Thread(target=ollama.serve_forever, name="ollama-mock", daemon=True).start()
    print(f"day9 bridge: mock ollama :11435, athena shim :8080, gt={GT_PATH}", flush=True)
    athena.serve_forever()


if __name__ == "__main__":
    main()
