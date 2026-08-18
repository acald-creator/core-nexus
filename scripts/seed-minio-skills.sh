#!/usr/bin/env bash
# seed-minio-skills.sh — Upload git-based skills to MinIO for the API Gateway.
#
# Usage:
#   ./scripts/seed-minio-skills.sh
#
# Requires: mc (MinIO client) configured with alias 'nexus'
# Or run after dev-stack.sh up — uses the compose MinIO instance.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MINIO_ALIAS="${MINIO_ALIAS:-nexus}"
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://localhost:9000}"
MINIO_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_PASS="${MINIO_ROOT_PASSWORD:-minioadmin}"
BUCKET="nexus-memory"
SKILLS_DIR="$REPO_ROOT/docs/skills"
SESSIONS_DIR="$REPO_ROOT/docs/skills/sessions"

# Ensure mc alias exists for local dev
mc alias set "$MINIO_ALIAS" "$MINIO_ENDPOINT" "$MINIO_USER" "$MINIO_PASS" 2>/dev/null || true

# Upload skills
echo "Uploading skills to MinIO..."
for f in "$SKILLS_DIR"/*.md; do
  [ -f "$f" ] || continue
  base="$(basename "$f")"
  [[ "$base" == "README.md" ]] && continue
  mc cp "$f" "$MINIO_ALIAS/$BUCKET/skills/$base"
done

# Upload session logs
echo "Uploading session logs to MinIO..."
for f in "$SESSIONS_DIR"/*.jsonl; do
  [ -f "$f" ] || continue
  mc cp "$f" "$MINIO_ALIAS/$BUCKET/sessions/$(basename "$f")"
done

echo "Done — skills and sessions uploaded to MinIO."
mc ls "$MINIO_ALIAS/$BUCKET/skills/" | head -5
