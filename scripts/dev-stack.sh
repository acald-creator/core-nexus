#!/usr/bin/env bash
# dev-stack.sh — Manage the unified Nexus compose stack.
#
# Usage:
#   ./scripts/dev-stack.sh up --from-vault   # preferred (secrets from HashiStack)
#   ./scripts/dev-stack.sh up               # offline defaults (changeme/minioadmin)
#   ./scripts/dev-stack.sh down|logs|status|build
#
# --from-vault loads secrets from nexus-hashistack export:
#   NEXUS_VAULT_ENV=/path/to/.env.core-nexus
#   or ../nexus-hashistack/.env.core-nexus
#   or ./.env.vault
#
# Set NEXUS_REQUIRE_VAULT=1 to refuse `up` without --from-vault / a vault env file.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/deploy/compose/dev.yml"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Error: compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

CMD="${1:-status}"
shift || true
FROM_VAULT=0
for arg in "$@"; do
  case "$arg" in
    --from-vault) FROM_VAULT=1 ;;
  esac
done

resolve_vault_env() {
  if [[ -n "${NEXUS_VAULT_ENV:-}" && -f "${NEXUS_VAULT_ENV}" ]]; then
    echo "$NEXUS_VAULT_ENV"
    return
  fi
  local cand
  for cand in \
    "$REPO_ROOT/.env.vault" \
    "$REPO_ROOT/../nexus-hashistack/.env.core-nexus" \
    "$HOME/nexus-hashistack/.env.core-nexus"
  do
    if [[ -f "$cand" ]]; then
      echo "$cand"
      return
    fi
  done
  return 1
}

case "$CMD" in
  up)
    COMPOSE=(docker compose)
    if [[ "$FROM_VAULT" == "1" ]]; then
      if ! VAULT_ENV="$(resolve_vault_env)"; then
        echo "Error: --from-vault set but no env file found." >&2
        echo "Run in nexus-hashistack: ./scripts/export-core-nexus-env.sh" >&2
        echo "Then set NEXUS_VAULT_ENV or copy to $REPO_ROOT/.env.vault" >&2
        exit 1
      fi
      echo "Using Vault-exported env: $VAULT_ENV"
      COMPOSE+=(--env-file "$VAULT_ENV")
    elif [[ "${NEXUS_REQUIRE_VAULT:-}" == "1" ]]; then
      echo "Error: NEXUS_REQUIRE_VAULT=1 but --from-vault was not set." >&2
      echo "Preferred lab flow:" >&2
      echo "  cd ../nexus-hashistack && ./scripts/nexus-dev-up.sh" >&2
      echo "  ./scripts/admin-bootstrap-approle.sh && ./scripts/export-core-nexus-env.sh" >&2
      echo "  cp .env.core-nexus ../core-nexus/.env.vault" >&2
      echo "  cd ../core-nexus && ./scripts/dev-stack.sh up --from-vault" >&2
      exit 1
    else
      echo "Note: starting with compose defaults (no Vault export)." >&2
      echo "      Prefer: ./scripts/dev-stack.sh up --from-vault" >&2
    fi
    echo "Starting Nexus dev stack..."
    "${COMPOSE[@]}" -f "$COMPOSE_FILE" up -d
    echo ""
    echo "Services:"
    echo "  Console:      http://localhost:3000"
    echo "  API Gateway:  http://localhost:3100 (docs: http://localhost:3100/docs)"
    echo "  MinIO:        http://localhost:9001 (minioadmin/minioadmin)"
    echo "  AI Inference:  http://localhost:8000 (docs: http://localhost:8000/docs)"
    if [[ "$FROM_VAULT" == "1" ]]; then
      echo "  Vault:        http://localhost:8200 (via nexus-hashistack)"
    fi
    echo ""
    "${COMPOSE[@]}" -f "$COMPOSE_FILE" ps
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
    echo "Usage: $0 {up|down|logs|status|build} [--from-vault]" >&2
    echo "  Prefer: $0 up --from-vault" >&2
    echo "  Strict: NEXUS_REQUIRE_VAULT=1 $0 up --from-vault" >&2
    exit 1
    ;;
esac
