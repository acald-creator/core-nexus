#!/usr/bin/env bash
# Day 14 Use: hybrid-sensor stack + labeled Athena traffic + triage in Console path.
#
# Prerequisites:
#   - hybrid-sensor overlay applied (see deploy/kubernetes/soc/overlays/hybrid-sensor/README.md)
#   - Purple target reachable (default Night Quire API on 127.0.0.1:8090)
#
# Usage:
#   ./scripts/day14-hybrid-soc-use.sh
#   ./scripts/day14-hybrid-soc-use.sh --skip-probe   # verify stack only
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_PROBE=0
TARGET_HOST="${ATHENA_TARGET_HOST:-127.0.0.1}"
TARGET_PORT="${ATHENA_TARGET_PORT:-8090}"
SCENARIO_LABEL="${ATHENA_SCENARIO_LABEL:-night-quire-recon}"
GT_OUTPUT="${ATHENA_GT_OUTPUT:-/tmp/day14-gt.jsonl}"
PF_GW="${DAY14_GW_PORT:-13100}"
PF_AI="${DAY14_AI_PORT:-18000}"

for arg in "$@"; do
  case "$arg" in
    --skip-probe) SKIP_PROBE=1 ;;
  esac
done

echo "== Day 14: hybrid SOC baseline check =="
kubectl -n soc get deploy nexus-api-gateway nexus-console ai-inference 2>/dev/null || {
  echo "SOC namespace not ready — apply hybrid-sensor overlay first." >&2
  exit 1
}

ALERTS_SOURCE="$(kubectl -n soc get deploy nexus-api-gateway -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="NEXUS_GW_ALERTS_SOURCE")].value}' 2>/dev/null || true)"
echo "Gateway alerts_source: ${ALERTS_SOURCE:-unknown}"

pkill -f "port-forward svc/nexus-api-gateway ${PF_GW}:" 2>/dev/null || true
pkill -f "port-forward svc/ai-inference ${PF_AI}:" 2>/dev/null || true
sleep 1
kubectl -n soc port-forward "svc/nexus-api-gateway" "${PF_GW}:3100" >/tmp/day14-pf-gw.log 2>&1 &
kubectl -n soc port-forward "svc/ai-inference" "${PF_AI}:8000" >/tmp/day14-pf-ai.log 2>&1 &
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

SCENARIO_ID="$(echo "$SESSION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["scenario_id"])')"
echo ""
echo "== Labeled probe complete =="
echo "$SESSION_JSON"

echo ""
echo "== Day 15 correlation export =="
"$ROOT/scripts/day15-correlate-session.sh" \
  --gt "$GT_OUTPUT" \
  --scenario-id "$SCENARIO_ID" \
  --inference-url "http://127.0.0.1:${PF_AI}" \
  --gateway-url "http://127.0.0.1:${PF_GW}"

echo ""
echo "Console (port-forward): kubectl -n soc port-forward svc/nexus-console 3000:80"
echo "Gateway alerts: curl -H \"Authorization: Bearer <token>\" http://127.0.0.1:${PF_GW}/api/v1/alerts"
