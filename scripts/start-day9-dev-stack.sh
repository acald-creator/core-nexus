#!/usr/bin/env bash
# Temporary Agent Feed lab: Gateway + Day9 bridge + Vite Console.
#
# The Day9 bridge (scripts/day9-console-bridge.py) mocks athena-agents HTTP on
# :8080 until the real athena-agents service exposes /sessions and /events.
# Replace this script when that HTTP API lands; do not treat it as production.
#
# Usage:
#   NEXUS_ENABLE_DAY9_BRIDGE=1 ./scripts/start-day9-dev-stack.sh
#
# Compose (`dev-stack.sh up`) does NOT start this bridge. Agent Feed against
# compose alone needs either this script or a real athena-agents on
# NEXUS_GW_ATHENA_AGENTS_URL (default host.docker.internal:8080).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GW_DIR="$ROOT/platform/api-gateway"
CONSOLE_DIR="$ROOT/platform/nexus-console"
BRIDGE="$ROOT/scripts/day9-console-bridge.py"
GT_PATH="${ATHENA_GT_OUTPUT:-/tmp/juice-shop-day9-gt.jsonl}"
SESSION_ID="${ATHENA_DAY9_SESSION:-day9-live}"
GW_LOG="${DAY9_GW_LOG:-/tmp/nexus-gw-day9.log}"
BRIDGE_LOG="${DAY9_BRIDGE_LOG:-/tmp/day9-bridge.log}"
CONSOLE_LOG="${DAY9_CONSOLE_LOG:-/tmp/nexus-console-day9.log}"
CONSOLE_PORT="${NEXUS_CONSOLE_PORT:-5174}"

if [[ "${NEXUS_ENABLE_DAY9_BRIDGE:-}" != "1" ]]; then
  echo "Refusing to start: set NEXUS_ENABLE_DAY9_BRIDGE=1 to acknowledge the temporary bridge." >&2
  echo "  NEXUS_ENABLE_DAY9_BRIDGE=1 $0" >&2
  echo "Or point NEXUS_GW_ATHENA_AGENTS_URL at a real athena-agents HTTP API." >&2
  exit 1
fi

port_listen() {
  lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null || true
}

free_port() {
  local port="$1"
  local pids
  pids="$(port_listen "$port")"
  if [[ -n "$pids" ]]; then
    echo "Stopping process on :$port ($pids)"
    kill $pids 2>/dev/null || true
    sleep 1
  fi
}

start_if_down() {
  local port="$1"
  local label="$2"
  shift 2
  if [[ -n "$(port_listen "$port")" ]]; then
    echo "$label already on :$port (pid $(port_listen "$port"))"
    return 0
  fi
  echo "Starting $label on :$port"
  "$@" &
  disown
}

export NEXUS_GW_JWT_SECRET="${NEXUS_GW_JWT_SECRET:-dev-secret-do-not-use-in-production}"
export NEXUS_GW_WAZUH_API_URL="${NEXUS_GW_WAZUH_API_URL:-https://wazuh-manager:55000}"
export NEXUS_GW_WAZUH_API_PASSWORD="${NEXUS_GW_WAZUH_API_PASSWORD:-changeme}"
export NEXUS_GW_MINIO_ACCESS_KEY="${NEXUS_GW_MINIO_ACCESS_KEY:-minioadmin}"
export NEXUS_GW_MINIO_SECRET_KEY="${NEXUS_GW_MINIO_SECRET_KEY:-minioadmin}"
export NEXUS_GW_MINIO_ENDPOINT="${NEXUS_GW_MINIO_ENDPOINT:-localhost:9000}"
export NEXUS_GW_MINIO_PUBLIC_ENDPOINT="${NEXUS_GW_MINIO_PUBLIC_ENDPOINT:-localhost:9000}"
export NEXUS_GW_AI_INFERENCE_URL="${NEXUS_GW_AI_INFERENCE_URL:-http://localhost:8000}"
export NEXUS_GW_ATHENA_AGENTS_URL="${NEXUS_GW_ATHENA_AGENTS_URL:-http://127.0.0.1:8080}"
export NEXUS_GW_CORS_ALLOWED_ORIGINS="${NEXUS_GW_CORS_ALLOWED_ORIGINS:-[\"http://localhost:3000\",\"http://localhost:5173\",\"http://localhost:5174\"]}"
export NEXUS_GW_DEBUG="${NEXUS_GW_DEBUG:-true}"
export NEXUS_GW_AUTH_PROVIDER="${NEXUS_GW_AUTH_PROVIDER:-local}"
export NEXUS_GW_SERVICE_REGISTRY_PATH="${NEXUS_GW_SERVICE_REGISTRY_PATH:-$GW_DIR/config/services.json}"

echo "NOTE: Day9 bridge is a temporary athena-agents HTTP shim — replace when real API exists."

if [[ -z "$(port_listen 3100)" ]]; then
  free_port 8080
  free_port 11435
  : > "$GT_PATH"
  start_if_down 3100 "API Gateway" bash -c "cd '$GW_DIR' && exec .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 3100 >>'$GW_LOG' 2>&1"
  export ATHENA_GT_OUTPUT="$GT_PATH"
  export ATHENA_DAY9_SESSION="$SESSION_ID"
  start_if_down 8080 "Day9 bridge" bash -c "exec python3 '$BRIDGE' >>'$BRIDGE_LOG' 2>&1"
fi

start_if_down "$CONSOLE_PORT" "Nexus Console" bash -c "cd '$CONSOLE_DIR' && exec npm run dev -- --port $CONSOLE_PORT --strictPort --host 127.0.0.1 >>'$CONSOLE_LOG' 2>&1"

for _ in $(seq 1 30); do
  gw_ok=0 console_ok=0
  curl -sf -m 1 "http://127.0.0.1:3100/healthz" >/dev/null 2>&1 && gw_ok=1
  curl -sf -m 1 "http://127.0.0.1:${CONSOLE_PORT}/" >/dev/null 2>&1 && console_ok=1
  if [[ "$gw_ok" -eq 1 && "$console_ok" -eq 1 ]]; then
    echo "Ready (temporary Day9 lab):"
    echo "  Console: http://127.0.0.1:${CONSOLE_PORT}/agent-feed"
    echo "  Gateway: http://127.0.0.1:3100"
    echo "  Bridge:  http://127.0.0.1:8080  (mock athena-agents)"
    echo "  Logs: $GW_LOG, $BRIDGE_LOG, $CONSOLE_LOG"
    exit 0
  fi
  sleep 1
done

echo "Timed out waiting for Gateway/Console. Check logs: $GW_LOG $CONSOLE_LOG" >&2
exit 1
