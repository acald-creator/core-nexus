#!/usr/bin/env bash
# Day 22 Use: deploy 3 Athena SQLi Suricata rules and verify against Juice Shop.
#
# Rules (athena.rules): SIDs 20262201–20262203 — body tautology, body quote-OR--,
# URI %27 on /rest/products/search. Reuses Day 21 in-cluster probe path.
#
# Usage:
#   ./scripts/day22-athena-sqli-rules.sh
#   ./scripts/day22-athena-sqli-rules.sh --skip-apply
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_APPLY=0
NS="${DAY22_NS:-soc}"
ALERTS_OUT="${DAY22_ALERTS_OUT:-/tmp/day22-suricata-alerts.jsonl}"
GT_OUTPUT="${ATHENA_GT_OUTPUT:-/tmp/day22-gt.jsonl}"

for arg in "$@"; do
  case "$arg" in
    --skip-apply) SKIP_APPLY=1 ;;
  esac
done

echo "== Day 22: Athena SQLi Suricata rules =="

if [[ "$SKIP_APPLY" != "1" ]]; then
  echo "Applying Suricata ConfigMap + DaemonSet..."
  kubectl apply -k "$ROOT/deploy/kubernetes/system/suricata" -n "$NS"
  kubectl -n "$NS" rollout restart daemonset/suricata
  kubectl -n "$NS" rollout status daemonset/suricata --timeout=180s
  # Engine start ≠ ready to inspect; Day 21 race left zero alerts after 5s.
  echo "Waiting for Suricata engine settle..."
  sleep 25
fi

SURICATA_POD="$(kubectl -n "$NS" get pod -l app.kubernetes.io/name=suricata -o jsonpath='{.items[0].metadata.name}')"
echo "Suricata pod: $SURICATA_POD"

# Confirm new SIDs loaded
echo "Loaded Athena SIDs (rules dump):"
kubectl -n "$NS" exec "$SURICATA_POD" -c suricata -- \
  suricatasc -c "ruleset-stat" 2>/dev/null | head -5 || true
kubectl -n "$NS" exec "$SURICATA_POD" -c suricata -- \
  grep -E "sid:2026220" /etc/suricata/athena.rules || {
  echo "ERROR: 2026220x SIDs not mounted in athena.rules" >&2
  exit 1
}

baseline="$(kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep -c "\"signature_id\":2026220" /var/log/suricata/eve.json 2>/dev/null || echo 0' | tr -d '[:space:]')"
echo "Baseline Day 22 SID alerts: $baseline"

export ATHENA_GT_OUTPUT="$GT_OUTPUT"
export DAY21_ALERTS_OUT="/tmp/day22-day21-sidecar-alerts.jsonl"
export ATHENA_SCENARIO_LABEL="${ATHENA_SCENARIO_LABEL:-juice-shop-sqli-day22}"
"$ROOT/scripts/day21-juice-sqli-suricata.sh"

echo ""
echo "== Day 22 SID extract (20262201–203) =="
sleep 2
: >"$ALERTS_OUT"
kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep "\"signature_id\":2026220" /var/log/suricata/eve.json 2>/dev/null | tail -80' \
  | tee "$ALERTS_OUT" || true

after="$(kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep -c "\"signature_id\":2026220" /var/log/suricata/eve.json 2>/dev/null || echo 0' | tr -d '[:space:]')"
echo "Day 22 SID alerts: baseline=$baseline after=$after"

python3 - <<PY
import json, collections, sys
from pathlib import Path
p = Path("$ALERTS_OUT")
counts = collections.Counter()
msgs = collections.Counter()
ifaces = collections.Counter()
for line in p.read_text().splitlines():
    if not line.strip():
        continue
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    alert = ev.get("alert") or {}
    sid = alert.get("signature_id")
    counts[sid] += 1
    msgs[alert.get("signature")] += 1
    ifaces[ev.get("in_iface")] += 1
print("SID counts:", dict(counts))
print("signatures:", dict(msgs))
print("ifaces:", dict(ifaces))
needed = {20262201, 20262202, 20262203}
missing = needed - set(counts)
if missing:
    print(f"FAIL: missing SIDs {sorted(missing)}", file=sys.stderr)
    sys.exit(1)
print("OK: all three Day 22 SIDs fired")
PY

echo "Alerts extract: $ALERTS_OUT"
echo "GT: $GT_OUTPUT"
