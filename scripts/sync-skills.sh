#!/usr/bin/env bash
# sync-skills.sh — Synchronize agent skill files between git, local, and MinIO.
#
# Usage:
#   ./scripts/sync-skills.sh push-local   # git → ~/.kiro/skills/
#   ./scripts/sync-skills.sh pull-local   # ~/.kiro/skills/ → git
#   ./scripts/sync-skills.sh push-minio   # git → MinIO nexus-memory/skills/
#   ./scripts/sync-skills.sh pull-minio   # MinIO nexus-memory/skills/ → git
#   ./scripts/sync-skills.sh status       # show diff between locations
#
# Environment variables:
#   MINIO_ALIAS     — mc alias name (default: nexus)
#   MINIO_BUCKET    — bucket path (default: nexus-memory/skills)
#   SKILLS_GIT_DIR  — git skills directory (default: docs/skills)
#   SKILLS_LOCAL    — local skills directory (default: ~/.kiro/skills)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MINIO_ALIAS="${MINIO_ALIAS:-nexus}"
MINIO_BUCKET="${MINIO_BUCKET:-nexus-memory/skills}"
SKILLS_GIT_DIR="${SKILLS_GIT_DIR:-$REPO_ROOT/docs/skills}"
SKILLS_LOCAL="${SKILLS_LOCAL:-$HOME/.kiro/skills}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[sync]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[sync]${NC} $*"; }
log_error() { echo -e "${RED}[sync]${NC} $*" >&2; }

# Ensure directories exist
ensure_dirs() {
    mkdir -p "$SKILLS_LOCAL"
    mkdir -p "$SKILLS_GIT_DIR"
}

# Push from git to local (~/.kiro/skills/)
push_local() {
    ensure_dirs
    local count=0
    for f in "$SKILLS_GIT_DIR"/*.md; do
        [ -f "$f" ] || continue
        base="$(basename "$f")"
        # Skip README
        [[ "$base" == "README.md" ]] && continue
        cp "$f" "$SKILLS_LOCAL/$base"
        count=$((count + 1))
    done
    log_info "Pushed $count skills from git → $SKILLS_LOCAL"
}

# Pull from local (~/.kiro/skills/) to git
pull_local() {
    ensure_dirs
    local count=0
    for f in "$SKILLS_LOCAL"/*.md; do
        [ -f "$f" ] || continue
        base="$(basename "$f")"
        cp "$f" "$SKILLS_GIT_DIR/$base"
        count=$((count + 1))
    done
    log_info "Pulled $count skills from $SKILLS_LOCAL → git"
    log_info "Remember to commit: git add docs/skills/ && git commit -m 'docs: update skills'"
}

# Push from git to MinIO
push_minio() {
    if ! command -v mc &>/dev/null; then
        log_error "MinIO client (mc) not found. Install: brew install minio/stable/mc"
        exit 1
    fi

    local count=0
    for f in "$SKILLS_GIT_DIR"/*.md; do
        [ -f "$f" ] || continue
        base="$(basename "$f")"
        [[ "$base" == "README.md" ]] && continue
        mc cp "$f" "$MINIO_ALIAS/$MINIO_BUCKET/$base"
        count=$((count + 1))
    done
    log_info "Pushed $count skills from git → MinIO ($MINIO_ALIAS/$MINIO_BUCKET)"
}

# Pull from MinIO to git
pull_minio() {
    if ! command -v mc &>/dev/null; then
        log_error "MinIO client (mc) not found. Install: brew install minio/stable/mc"
        exit 1
    fi

    local count=0
    local tmp_dir
    tmp_dir="$(mktemp -d)"
    mc cp --recursive "$MINIO_ALIAS/$MINIO_BUCKET/" "$tmp_dir/"

    for f in "$tmp_dir"/*.md; do
        [ -f "$f" ] || continue
        base="$(basename "$f")"
        cp "$f" "$SKILLS_GIT_DIR/$base"
        count=$((count + 1))
    done
    rm -rf "$tmp_dir"
    log_info "Pulled $count skills from MinIO → git"
    log_info "Remember to commit: git add docs/skills/ && git commit -m 'docs: update skills from MinIO'"
}

# Show status/diff between locations
show_status() {
    ensure_dirs
    echo ""
    log_info "=== Skill Sync Status ==="
    echo ""

    # Git skills
    local git_count=0
    for f in "$SKILLS_GIT_DIR"/*.md; do
        [ -f "$f" ] && [[ "$(basename "$f")" != "README.md" ]] && git_count=$((git_count + 1))
    done
    echo "  Git (docs/skills/):     $git_count skills"

    # Local skills
    local local_count=0
    for f in "$SKILLS_LOCAL"/*.md; do
        [ -f "$f" ] && local_count=$((local_count + 1))
    done
    echo "  Local (~/.kiro/skills/): $local_count skills"

    # MinIO (if mc available)
    if command -v mc &>/dev/null; then
        local minio_count
        minio_count=$(mc ls "$MINIO_ALIAS/$MINIO_BUCKET/" 2>/dev/null | grep -c "\.md$" || echo "0")
        echo "  MinIO ($MINIO_BUCKET):   $minio_count skills"
    else
        echo "  MinIO: (mc not installed)"
    fi

    echo ""

    # Show differences
    log_info "=== Only in Git (not in local) ==="
    for f in "$SKILLS_GIT_DIR"/*.md; do
        [ -f "$f" ] || continue
        base="$(basename "$f")"
        [[ "$base" == "README.md" ]] && continue
        if [ ! -f "$SKILLS_LOCAL/$base" ]; then
            echo "  + $base"
        fi
    done

    log_info "=== Only in Local (not in git) ==="
    for f in "$SKILLS_LOCAL"/*.md; do
        [ -f "$f" ] || continue
        base="$(basename "$f")"
        if [ ! -f "$SKILLS_GIT_DIR/$base" ]; then
            echo "  + $base"
        fi
    done

    echo ""
}

# Main dispatch
case "${1:-status}" in
    push-local)  push_local ;;
    pull-local)  pull_local ;;
    push-minio)  push_minio ;;
    pull-minio)  pull_minio ;;
    status)      show_status ;;
    *)
        echo "Usage: $0 {push-local|pull-local|push-minio|pull-minio|status}"
        exit 1
        ;;
esac
