#!/usr/bin/env python3
"""Minimal labeled Athena probe session for Day 14 hybrid-SOC lab use.

Host-native HTTP to an allowlisted target does not always traverse Suricata/Vector
(see platform/athena/README). This script:
  1. Emits OPAR-shaped ground-truth JSONL for nexus-tui / purple eval
  2. Sends labeled GET probes with X-Athena-* headers
  3. POSTs normalized events to ai-inference /v1/triage (Vector-equivalent lab path)

Not a substitute for full OPAR when Ollama is available — use orchestrator for that.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_PATHS = (
    "/health",
    "/api/v1/novels",
    "/api/v1/home",
    "/api/v1/search?q=test",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _http_get(url: str, headers: dict[str, str], timeout: float) -> tuple[int, str]:
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read(4096).decode("utf-8", errors="replace")
            return resp.status, body[:200]
    except HTTPError as exc:
        body = exc.read(4096).decode("utf-8", errors="replace")
        return exc.code, body[:200]
    except URLError as exc:
        raise RuntimeError(f"GET {url} failed: {exc}") from exc


def _post_triage(base_url: str, event: dict) -> dict:
    payload = json.dumps(event).encode("utf-8")
    req = Request(
        f"{base_url.rstrip('/')}/v1/triage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a labeled probe session (Day 14 lab)")
    parser.add_argument("--target-host", default="127.0.0.1")
    parser.add_argument("--target-port", type=int, default=8090)
    parser.add_argument("--scenario-label", default="night-quire-recon")
    parser.add_argument("--scenario-id", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--technique", default="T1595")
    parser.add_argument("--gt-output", default="/tmp/day14-gt.jsonl")
    parser.add_argument("--inference-url", default="http://127.0.0.1:18000")
    parser.add_argument("--skip-triage", action="store_true")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    scenario_id = args.scenario_id or str(uuid.uuid4())
    run_id = args.run_id or f"run-{uuid.uuid4().hex[:8]}"
    gt_path = Path(args.gt_output)
    gt_path.parent.mkdir(parents=True, exist_ok=True)

    base = f"http://{args.target_host}:{args.target_port}"
    label_headers = {
        "X-Athena-Scenario": args.scenario_label,
        "X-Athena-Scenario-Id": scenario_id,
        "X-Athena-Run-ID": run_id,
        "User-Agent": "athena-agents/labeled-probe-session",
    }

    events: list[dict] = []
    triage_ids: list[str] = []

    def append_gt(phase: str, summary: str, tool: str = "", label: str = "malicious") -> None:
        row = {
            "timestamp": _now_iso(),
            "phase": phase,
            "scenario_id": scenario_id,
            "run_id": run_id,
            "target": f"{args.target_host}:{args.target_port}",
            "summary": summary,
            "technique": args.technique,
            "label": label,
        }
        if tool:
            row["tool"] = tool
        events.append(row)
        with gt_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")

    append_gt("observe", f"Starting labeled recon against {base}", label="benign_control")
    append_gt("plan", f"Selected GET probes on public API paths ({args.technique})", label="benign_control")

    for path in DEFAULT_PATHS:
        url = base + path
        status, snippet = _http_get(url, label_headers, args.timeout)
        summary = f"GET {path} → HTTP {status}"
        append_gt("act", summary, tool="http-request", label="malicious")

        if not args.skip_triage:
            event_id = str(uuid.uuid4())
            triage_event = {
                "source_event_id": event_id,
                "timestamp": _now_iso(),
                "event_type": "Generic",
                "source": "athena",
                "nexus.source": "athena",
                "X-Athena-Scenario": args.scenario_label,
                "X-Athena-Scenario-Id": scenario_id,
                "scenario_id": scenario_id,
                "technique": args.technique,
                "data": {
                    "http_status": status,
                    "url": url,
                    "summary": summary,
                    "headers": label_headers,
                },
            }
            try:
                result = _post_triage(args.inference_url, triage_event)
                triage_ids.append(result.get("source_event_id") or event_id)
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                print(f"warning: triage POST failed for {path}: {exc}", file=sys.stderr)

    append_gt(
        "reflect",
        f"Completed {len(DEFAULT_PATHS)} labeled GET probes; triage posts={len(triage_ids)}",
        label="successful_simulation",
    )

    print(json.dumps({
        "scenario_id": scenario_id,
        "run_id": run_id,
        "scenario_label": args.scenario_label,
        "gt_output": str(gt_path),
        "opar_events": len(events),
        "triage_posts": len(triage_ids),
        "triage_ids": triage_ids[:10],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
