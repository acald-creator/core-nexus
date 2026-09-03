#!/usr/bin/env bash
# Day 15: export Console-equivalent alerts + nexus-tui feeds for the same session.
#
# Usage:
#   ./scripts/day15-correlate-session.sh \
#     --gt /tmp/day14-gt.jsonl \
#     --scenario-id <uuid> \
#     --inference-url http://127.0.0.1:18000 \
#     --gateway-url http://127.0.0.1:13100
#
# Writes:
#   /tmp/day15-agent-log.jsonl   → NEXUS_AGENT_LOG
#   /tmp/day15-alerts.jsonl      → NEXUS_ALERTS_FILE
#   /tmp/day15-correlation.json  → match summary
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GT_FILE=""
SCENARIO_ID=""
INFERENCE_URL="${ATHENA_INFERENCE_URL:-http://127.0.0.1:18000}"
GATEWAY_URL="${NEXUS_GATEWAY_URL:-http://127.0.0.1:13100}"
AGENT_OUT="/tmp/day15-agent-log.jsonl"
ALERTS_OUT="/tmp/day15-alerts.jsonl"
REPORT_OUT="/tmp/day15-correlation.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gt) GT_FILE="$2"; shift 2 ;;
    --scenario-id) SCENARIO_ID="$2"; shift 2 ;;
    --inference-url) INFERENCE_URL="$2"; shift 2 ;;
    --gateway-url) GATEWAY_URL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$GT_FILE" || ! -f "$GT_FILE" ]]; then
  echo "Missing --gt file" >&2
  exit 1
fi

if [[ -z "$SCENARIO_ID" ]]; then
  SCENARIO_ID="$(python3 - <<'PY' "$GT_FILE"
import json, sys
from pathlib import Path
for line in Path(sys.argv[1]).read_text().splitlines():
    if not line.strip():
        continue
    data = json.loads(line)
    if data.get("scenario_id"):
        print(data["scenario_id"])
        break
PY
)"
fi

if [[ -z "$SCENARIO_ID" ]]; then
  echo "Could not infer scenario_id from GT file" >&2
  exit 1
fi

echo "Scenario: $SCENARIO_ID"
cp "$GT_FILE" "$AGENT_OUT"

python3 - <<'PY' "$INFERENCE_URL" "$SCENARIO_ID" "$ALERTS_OUT" "$REPORT_OUT" "$GT_FILE"
import json, sys, urllib.request
from pathlib import Path

inference_url, scenario_id, alerts_out, report_out, gt_file = sys.argv[1:6]
gt_rows = [json.loads(l) for l in Path(gt_file).read_text().splitlines() if l.strip()]
act_rows = [r for r in gt_rows if r.get("phase") == "act"]

req = urllib.request.Request(
    f"{inference_url.rstrip('/')}/v1/triage/recent?limit=500",
    headers={"Accept": "application/json"},
)
with urllib.request.urlopen(req, timeout=30) as resp:
    body = json.loads(resp.read().decode())

results = body.get("results") if isinstance(body, dict) else body
matched = []
for rec in results or []:
    meta = rec.get("feature_meta") if isinstance(rec.get("feature_meta"), dict) else {}
    sid = (
        rec.get("scenario_id")
        or rec.get("athena_scenario")
        or meta.get("scenario_id")
        or meta.get("athena_scenario")
    )
    if str(sid) == scenario_id:
        matched.append(rec)

alerts = []
for rec in matched:
    meta = rec.get("feature_meta") if isinstance(rec.get("feature_meta"), dict) else {}
    score = float(rec.get("score") or rec.get("confidenceScore") or 0.0)
    sev = "critical" if score >= 0.85 else "high" if score >= 0.7 else "medium" if score >= 0.5 else "low"
    alerts.append({
        "timestamp": rec.get("timestamp") or rec.get("saved_at"),
        "source": rec.get("source") or meta.get("nexus.source") or "ai-inference",
        "severity": sev,
        "rule_id": str(rec.get("source_event_id") or rec.get("id") or "")[:12],
        "title": rec.get("reason") or rec.get("reasoningExcerpt") or "AI triage",
        "labels": {"athena_scenario": scenario_id},
    })

Path(alerts_out).write_text("\n".join(json.dumps(a) for a in alerts) + ("\n" if alerts else ""), encoding="utf-8")

report = {
    "scenario_id": scenario_id,
    "ground_truth_act_events": len(act_rows),
    "triage_alerts_matched": len(alerts),
    "correlation_ratio": round(len(alerts) / max(len(act_rows), 1), 3),
    "agent_log": alerts_out.replace("day15-alerts.jsonl", "day15-agent-log.jsonl"),
    "alerts_file": alerts_out,
}
Path(report_out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
PY

echo ""
echo "TUI:"
echo "  NEXUS_AGENT_LOG=$AGENT_OUT NEXUS_ALERTS_FILE=$ALERTS_OUT go run ./cmd/nexus-tui"
echo ""
echo "Purple eval (optional):"
echo "  cd ../athena-agents && ATHENA_GT_OUTPUT=$GT_FILE ATHENA_INFERENCE_URL=$INFERENCE_URL python -m eval.purple_eval --gt $GT_FILE"
