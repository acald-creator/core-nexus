#!/usr/bin/env bash
# Day 19 Use: agent + monitor from terminal only (air-gapped simulation).
#
# No Console, no browser. Operator path is kubectl + curl + labeled probes + nexus-tui.
# Air-gap *delivery* is Zarf (`deploy/uds/`) — optional --uds-create.
#
# Usage:
#   ./scripts/day19-airgap-terminal.sh
#   ./scripts/day19-airgap-terminal.sh --skip-probe
#   ./scripts/day19-airgap-terminal.sh --uds-create
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_PROBE=0
UDS_CREATE=0
TARGET_HOST="${ATHENA_TARGET_HOST:-127.0.0.1}"
TARGET_PORT="${ATHENA_TARGET_PORT:-8090}"
SCENARIO_LABEL="${ATHENA_SCENARIO_LABEL:-night-quire-airgap}"
GT_OUTPUT="${ATHENA_GT_OUTPUT:-/tmp/day19-gt.jsonl}"
PF_AI="${DAY19_AI_PORT:-18000}"
SKILLS_DIR="${NEXUS_SKILLS_DIR:-$ROOT/docs/skills}"

for arg in "$@"; do
  case "$arg" in
    --skip-probe) SKIP_PROBE=1 ;;
    --uds-create) UDS_CREATE=1 ;;
  esac
done

echo "== Day 19: terminal-only air-gap simulation =="
echo "Surfaces in this run: kubectl, curl, python, nexus-tui --dump"
echo "Not used: Nexus Console, browser, Gateway login"

if [[ "$UDS_CREATE" == "1" ]]; then
  echo ""
  echo "== UDS / Zarf package create =="
  "$ROOT/deploy/uds/create-packages.sh"
fi

if [[ -d "$ROOT/dist/uds" ]]; then
  echo ""
  echo "== Zarf artifacts (offline media) =="
  ls -lh "$ROOT/dist/uds"/zarf-package-*.tar.zst 2>/dev/null || ls -lh "$ROOT/dist/uds" 2>/dev/null || true
fi

echo ""
echo "== Cluster (ai-inference only; no Console port-forward) =="
kubectl -n soc get deploy ai-inference >/dev/null 2>&1 || {
  echo "ai-inference not in soc — hybrid-sensor / Zarf platform package not applied." >&2
  echo "For a file-only dump demo: NEXUS_AGENT_LOG=cmd/nexus-tui/testdata/agent-log.jsonl go run ./cmd/nexus-tui --dump" >&2
  exit 1
}

pkill -f "port-forward svc/ai-inference ${PF_AI}:" 2>/dev/null || true
sleep 1
kubectl -n soc port-forward "svc/ai-inference" "${PF_AI}:8000" >/tmp/day19-pf-ai.log 2>&1 &
sleep 2
HEALTH="$(curl -sf "http://127.0.0.1:${PF_AI}/health" || echo '{}')"
echo "ai-inference health: $HEALTH"

if [[ "$SKIP_PROBE" == "1" ]]; then
  echo "Skipping labeled probe (--skip-probe)."
  exit 0
fi

if ! curl -sf "http://${TARGET_HOST}:${TARGET_PORT}/health" >/dev/null; then
  echo "Target http://${TARGET_HOST}:${TARGET_PORT}/health not reachable." >&2
  echo "Start Night Quire API or set ATHENA_TARGET_HOST/PORT." >&2
  exit 1
fi

: >"$GT_OUTPUT"
SESSION_JSON="$(
  python3 "$ROOT/scripts/labeled-probe-session.py" \
    --target-host "$TARGET_HOST" \
    --target-port "$TARGET_PORT" \
    --scenario-label "$SCENARIO_LABEL" \
    --gt-output "$GT_OUTPUT" \
    --inference-url "http://127.0.0.1:${PF_AI}"
)"
echo "$SESSION_JSON"
SCENARIO_ID="$(echo "$SESSION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["scenario_id"])')"

echo ""
echo "== Correlate GT → TUI files (no Gateway) =="
"$ROOT/scripts/day15-correlate-session.sh" \
  --gt "$GT_OUTPUT" \
  --scenario-id "$SCENARIO_ID" \
  --inference-url "http://127.0.0.1:${PF_AI}"

# Reuse day15 output paths; copy to day19 names for the TUI dump.
cp /tmp/day15-agent-log.jsonl /tmp/day19-agent-log.jsonl
cp /tmp/day15-alerts.jsonl /tmp/day19-alerts.jsonl

echo ""
echo "== nexus-tui --dump (no alt-screen) =="
(
  cd "$ROOT/cmd/nexus-tui"
  NEXUS_AGENT_LOG=/tmp/day19-agent-log.jsonl \
  NEXUS_ALERTS_FILE=/tmp/day19-alerts.jsonl \
  NEXUS_SKILLS_DIR="$SKILLS_DIR" \
    go run . --dump
)

echo ""
echo "Interactive TUI (optional, still no Console):"
echo "  NEXUS_AGENT_LOG=/tmp/day19-agent-log.jsonl NEXUS_ALERTS_FILE=/tmp/day19-alerts.jsonl NEXUS_SKILLS_DIR=$SKILLS_DIR go run .  # from cmd/nexus-tui"
echo ""
echo "Air-gap delivery (if packages exist):"
echo "  zarf package deploy dist/uds/zarf-package-nexus-platform-*.tar.zst --confirm"
echo "  zarf package deploy dist/uds/zarf-package-nexus-hybrid-sensor-*.tar.zst --confirm"
echo "  zarf package deploy dist/uds/zarf-package-nexus-airgap-ops-*.tar.zst --confirm"
