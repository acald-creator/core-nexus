#!/usr/bin/env bash
# Day 25 Use: tune Suricata Athena rules for fewer FPs, re-probe, compare volume.
#
# Expect after tune (one dir-bruteforce-sized storm ~23 GETs):
#   20262401 (storm, threshold both 8/30s)  ≪ wordlist size (often 1–3)
#   20262402 / 20262403                     ≤1 each (UA-gated)
#   20261601 / 20261602                     ≤1 each per src / 120s (limit)
#
# Day 24 baseline: 20262401 fired once per GET (~46 in one run).
#
# Usage:
#   ./scripts/day25-suricata-fp-tune.sh
#   ./scripts/day25-suricata-fp-tune.sh --skip-apply
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_APPLY=0
NS="${SURICATA_NS:-soc}"
ALERTS_OUT="${DAY25_ALERTS_OUT:-/tmp/day25-suricata-alerts.jsonl}"
JUICE_PORT="${JUICE_PORT:-3003}"
JUICE_HOST="${JUICE_HOST:-host.docker.internal}"
JUICE_BASE="http://${JUICE_HOST}:${JUICE_PORT}"

for arg in "$@"; do
  case "$arg" in
    --skip-apply) SKIP_APPLY=1 ;;
  esac
done

echo "== Day 25: Suricata FP tune (labeled + dir-bruteforce) =="

kubectl delete configmap suricata-config -n default --ignore-not-found >/dev/null 2>&1 || true

if [[ "$SKIP_APPLY" != "1" ]]; then
  echo "Applying Suricata ConfigMap + DaemonSet (ns=$NS)..."
  kubectl apply -k "$ROOT/deploy/kubernetes/system/suricata" -n "$NS"
  kubectl -n "$NS" rollout restart daemonset/suricata
  kubectl -n "$NS" rollout status daemonset/suricata --timeout=180s
  echo "Waiting for Suricata engine settle..."
  sleep 25
fi

SURICATA_POD="$(kubectl -n "$NS" get pod -l app.kubernetes.io/name=suricata -o jsonpath='{.items[0].metadata.name}')"
echo "Suricata pod: $SURICATA_POD"
kubectl -n "$NS" exec "$SURICATA_POD" -c suricata -- grep -E "sid:2026(16|22|24)0" /etc/suricata/athena.rules

if ! curl -sf -o /dev/null --connect-timeout 3 "http://127.0.0.1:${JUICE_PORT}/"; then
  echo "Juice Shop not on host :${JUICE_PORT}" >&2
  exit 1
fi

count_sids() {
  local pod="$1"
  kubectl -n "$NS" exec "$pod" -c log-tail -- sh -c \
    'grep -E "\"signature_id\":2026(160[123]|220[123]|240[123])" /var/log/suricata/eve.json 2>/dev/null | wc -l' \
    | tr -d '[:space:]' | grep -oE '[0-9]+' | tail -1
}

BASELINE="$(count_sids "$SURICATA_POD")"
echo "Baseline Athena SID alert lines: $BASELINE"

SCENARIO_ID="$(uuidgen | tr '[:upper:]' '[:lower:]')"
RUN_ID="run-$(uuidgen | tr '[:upper:]' '[:lower:]' | cut -c1-8)"
SCENARIO_LABEL="juice-shop-dirbrute-day25"

echo ""
echo "== In-cluster probe (same Day 24 capture path; ~23 GETs) =="
echo "Target: $JUICE_BASE scenario=$SCENARIO_LABEL id=$SCENARIO_ID"

kubectl -n "$NS" create configmap day25-dirbrute-probe-script \
  --from-file=probe.sh="$ROOT/scripts/day24-dirbrute-probe.sh" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "$NS" delete job day25-dirbrute-probe --ignore-not-found >/dev/null 2>&1 || true
cat <<EOF | kubectl -n "$NS" apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: day25-dirbrute-probe
  labels:
    app.kubernetes.io/name: day25-dirbrute-probe
spec:
  ttlSecondsAfterFinished: 180
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: probe
          image: curlimages/curl:8.5.0
          env:
            - name: BASE
              value: "${JUICE_BASE}"
            - name: SCENARIO
              value: "${SCENARIO_LABEL}"
            - name: SCENARIO_ID
              value: "${SCENARIO_ID}"
            - name: RUN_ID
              value: "${RUN_ID}"
          command: ["/bin/sh", "/scripts/probe.sh"]
          volumeMounts:
            - name: script
              mountPath: /scripts
      volumes:
        - name: script
          configMap:
            name: day25-dirbrute-probe-script
            defaultMode: 0755
EOF

kubectl -n "$NS" wait --for=condition=complete job/day25-dirbrute-probe --timeout=120s || {
  kubectl -n "$NS" logs job/day25-dirbrute-probe || true
  exit 1
}
kubectl -n "$NS" logs job/day25-dirbrute-probe
sleep 5

AFTER="$(count_sids "$SURICATA_POD")"
DELTA=$((AFTER - BASELINE))
echo ""
echo "Athena SID alert lines: baseline=$BASELINE after=$AFTER delta=$DELTA"

: >"$ALERTS_OUT"
kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep -E "\"signature_id\":2026(160[123]|220[123]|240[123])" /var/log/suricata/eve.json 2>/dev/null | tail -200' \
  >"$ALERTS_OUT" || true

python3 - <<PY
import json
from collections import Counter
from pathlib import Path

path = Path("$ALERTS_OUT")
c = Counter()
msgs = {}
rows = []
for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    a = o.get("alert") or {}
    sid = a.get("signature_id")
    if sid is None:
        continue
    c[sid] += 1
    msgs[sid] = a.get("signature", "")
    rows.append(o)

# Prefer last N events that include dir-bruteforce / day25 marker in http headers if present
marker = "$SCENARIO_ID"
focused = Counter()
for o in rows[-80:]:
    http = o.get("http") or {}
    blob = json.dumps(o)
    if marker[:8] in blob or "dir-bruteforce" in blob or "day25" in blob.lower():
        sid = (o.get("alert") or {}).get("signature_id")
        if sid is not None:
            focused[sid] += 1

print("Recent Athena SID histogram (last ~200 matching lines in eve):")
for sid in sorted(c):
    print(f"  {sid}: {c[sid]}  {msgs.get(sid, '')[:72]}")
print(f"file_total_lines={sum(c.values())} delta_vs_baseline={$DELTA}")
if focused:
    print("Focused (marker/dirbrute in payload):")
    for sid in sorted(focused):
        print(f"  {sid}: {focused[sid]}")
# Soft assert: 20262401 should not dominate like Day 24 (~1:1 with GETs)
ua = c.get(20262401, 0)
if ua > 15:
    print(f"WARN: 20262401 count {ua} still high in window (threshold may need settle/restart)")
else:
    print(f"OK: 20262401 volume look tuned (count in window={ua})")
PY

echo ""
echo "Wrote $ALERTS_OUT"
echo "Done. scenario_id=$SCENARIO_ID run_id=$RUN_ID"
