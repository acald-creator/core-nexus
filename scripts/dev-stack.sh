#!/usr/bin/env bash
# dev-stack.sh — Manage the unified dev compose stack.
#
# Usage:
#   ./scripts/dev-stack.sh up      # Start all services
#   ./scripts/dev-stack.sh down    # Stop all services
#   ./scripts/dev-stack.sh logs    # Follow all logs
#   ./scripts/dev-stack.sh status  # Show running services
#   ./scripts/dev-stack.sh build   # Rebuild images

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/deploy/compose/dev.yml"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Error: compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

CMD="${1:-status}"

case "$CMD" in
  up)
    echo "Starting Nexus dev stack..."
    docker compose -f "$COMPOSE_FILE" up -d
    echo ""
    echo "Services:"
    echo "  Console:      http://localhost:3000"
    echo "  API Gateway:  http://localhost:3100 (docs: http://localhost:3100/docs)"
    echo "  MinIO:        http://localhost:9001 (minioadmin/minioadmin)"
    echo "  AI Inference:  http://localhost:8000 (docs: http://localhost:8000/docs)"
    echo ""
    docker compose -f "$COMPOSE_FILE" ps
    ;;
  down)
    echo "Stopping Nexus dev stack..."
    docker compose -f "$COMPOSE_FILE" down
    ;;
  logs)
    docker compose -f "$COMPOSE_FILE" logs -f
    ;;
  status)
    docker compose -f "$COMPOSE_FILE" ps
    ;;
  build)
    echo "Rebuilding images..."
    docker compose -f "$COMPOSE_FILE" build
    ;;
  *)
    echo "Usage: $0 {up|down|logs|status|build}" >&2
    exit 1
    ;;
esac
