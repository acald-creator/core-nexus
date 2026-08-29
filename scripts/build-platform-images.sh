#!/usr/bin/env bash
# build-platform-images.sh - Build, SBOM, and scan all platform images.
#
# Tags match deploy/compose/dev.yml and deploy/kubernetes/soc/base:
#   phoenixvlabs/nexus-{console,api-gateway,ai-inference,mcp}:latest
#
# Usage:
#   ./scripts/build-platform-images.sh              # Build all
#   ./scripts/build-platform-images.sh console      # Build one
#   ./scripts/build-platform-images.sh --push       # Build + push all
#   REGISTRY=phoenixvlabs ./scripts/build-platform-images.sh --push
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PUSH=false
REGISTRY="${REGISTRY:-phoenixvlabs}"
SPECIFIC=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --push) PUSH=true; shift ;;
    --registry) REGISTRY="$2"; shift 2 ;;
    console|api-gateway|ai-inference|mcp) SPECIFIC="$1"; shift ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done
VERSION="$(git -C "$REPO_ROOT" log -1 --pretty=%h 2>/dev/null || echo dev)"
declare -A IMAGES
IMAGES[console]="$REPO_ROOT/platform/nexus-console"
IMAGES[api-gateway]="$REPO_ROOT/platform/api-gateway"
IMAGES[ai-inference]="$REPO_ROOT/platform/ai-inference"
IMAGES[mcp]="$REPO_ROOT/platform/mcp"
build_image() {
  local name="$1"
  local context="${IMAGES[$name]}"
  local tag="$REGISTRY/nexus-$name:$VERSION"
  local latest="$REGISTRY/nexus-$name:latest"
  if [[ ! -f "$context/Dockerfile" ]]; then
    echo "  SKIP $name (no Dockerfile)"
    return
  fi
  echo "  Building $name..."
  docker build -t "$tag" -t "$latest" "$context" 2>&1 | tail -3
  echo "  SBOM..."
  mkdir -p "$REPO_ROOT/supply-chain/sboms"
  syft "$tag" -o spdx-json="$REPO_ROOT/supply-chain/sboms/$name-$VERSION.spdx.json" 2>/dev/null
  echo "  Scan..."
  mkdir -p "$REPO_ROOT/supply-chain/scans"
  grype "$tag" -o json > "$REPO_ROOT/supply-chain/scans/$name-$VERSION.grype.json" 2>/dev/null || true
  if [ "$PUSH" = true ]; then
    echo "  Push..."
    docker push "$tag"
    docker push "$latest"
    if [ -n "${COSIGN_PRIVATE_KEY:-}" ]; then
      cosign sign --yes --key "$COSIGN_PRIVATE_KEY" -a commit="$VERSION" "$tag"
    fi
  fi
  echo "  Done: $tag"
}
echo "=== Platform Image Build ==="
echo "  Registry: $REGISTRY"
echo "  Version:  $VERSION"
echo "  Push:     $PUSH"
echo ""
if [ -n "$SPECIFIC" ]; then
  build_image "$SPECIFIC"
else
  for name in console api-gateway ai-inference mcp; do
    build_image "$name"
    echo ""
  done
fi
echo ""
echo "SBOMs: supply-chain/sboms/"
echo "Scans: supply-chain/scans/"
