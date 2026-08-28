#!/usr/bin/env bash
# Start Gateway + Day9 bridge + Nexus Console for local Agent Feed dev.
# Usage: ./scripts/start-day9-dev-stack.sh
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
export NEXUS_GW_SERVICE_REGISTRY_PATH="${NEXUS_GW_SERVICE_REGISTRY_PATH:-$GW_DIR/config/services.json}"

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
    echo "Ready:"
    echo "  Console: http://127.0.0.1:${CONSOLE_PORT}/agent-feed"
    echo "  Gateway: http://127.0.0.1:3100"
    echo "  Logs: $GW_LOG, $BRIDGE_LOG, $CONSOLE_LOG"
    exit 0
  fi
  sleep 0.5
done

echo "Stack did not become ready in time — check logs above" >&2
exit 1
