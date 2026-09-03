#!/usr/bin/env bash
# Build Zarf packages for hybrid-sensor + air-gap operator files.
# Image packages need a connected builder; nexus-airgap-ops is files-only.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${ZARF_OUT:-$ROOT/dist/uds}"
mkdir -p "$OUT"

if ! command -v zarf >/dev/null 2>&1; then
  echo "zarf CLI not on PATH. See deploy/uds/README.md (local build from ~/zarf)." >&2
  exit 1
fi

echo "== go build nexus-tui → $OUT/nexus-tui =="
(cd "$ROOT/cmd/nexus-tui" && go build -o "$OUT/nexus-tui" .)

echo "== zarf package create (airgap-ops, files) =="
zarf package create "$ROOT/deploy/uds/nexus-airgap-ops" -o "$OUT" --confirm

CREATE_IMAGES="${ZARF_CREATE_IMAGES:-0}"
if [[ "$CREATE_IMAGES" == "1" ]]; then
  echo "== zarf package create (platform + hybrid-sensor images) =="
  zarf package create "$ROOT/deploy/uds/nexus-platform" -o "$OUT" --confirm
  zarf package create "$ROOT/deploy/uds/nexus-hybrid-sensor" -o "$OUT" --confirm
else
  echo "Skipping image packages (set ZARF_CREATE_IMAGES=1 to pull Console/gateway/sensors into tarballs)."
  if compgen -G "$OUT/zarf-package-nexus-platform-*.tar.zst" >/dev/null; then
    zarf package inspect definition "$OUT"/zarf-package-nexus-platform-*.tar.zst
  fi
  if compgen -G "$OUT/zarf-package-nexus-hybrid-sensor-*.tar.zst" >/dev/null; then
    zarf package inspect definition "$OUT"/zarf-package-nexus-hybrid-sensor-*.tar.zst
  fi
  if compgen -G "$OUT/zarf-package-nexus-airgap-ops-*.tar.zst" >/dev/null; then
    zarf package inspect definition "$OUT"/zarf-package-nexus-airgap-ops-*.tar.zst
  fi
fi

echo ""
echo "Artifacts in $OUT:"
ls -lh "$OUT"
