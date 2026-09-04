#!/usr/bin/env bash
# Day 21 Use: Juice Shop SQLi stimulation + Suricata eve.json observation.
#
# Host-native curl to localhost does NOT cross Rancher vznat. This script probes
# Juice Shop via host.docker.internal from an in-cluster curl Job so Suricata
# (hostNetwork, eth0+vznat+cni0) can see the packets.
#
# Default: host.docker.internal:3003 (Juice Shop; :3001 may be occupied).
#
# Usage:
#   ./scripts/day21-juice-sqli-suricata.sh
#   ./scripts/day21-juice-sqli-suricata.sh --skip-probe
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_PROBE=0
GT_OUTPUT="${ATHENA_GT_OUTPUT:-/tmp/day21-gt.jsonl}"
ALERTS_OUT="${DAY21_ALERTS_OUT:-/tmp/day21-suricata-alerts.jsonl}"
SCENARIO_LABEL="${ATHENA_SCENARIO_LABEL:-juice-shop-sqli}"
NS="${DAY21_NS:-soc}"
JUICE_HOST="${JUICE_HOST:-host.docker.internal}"
JUICE_PORT="${JUICE_PORT:-3003}"
JUICE_BASE="http://${JUICE_HOST}:${JUICE_PORT}"

for arg in "$@"; do
  case "$arg" in
    --skip-probe) SKIP_PROBE=1 ;;
  esac
done

echo "== Day 21: Juice Shop SQLi → Suricata =="
echo "Target: $JUICE_BASE"

SURICATA_POD="$(kubectl -n "$NS" get pod -l app.kubernetes.io/name=suricata -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
if [[ -z "$SURICATA_POD" ]]; then
  echo "Suricata DaemonSet pod not found in $NS" >&2
  exit 1
fi
echo "Suricata pod: $SURICATA_POD"

baseline="$(kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep -c "\"signature_id\":2026160" /var/log/suricata/eve.json 2>/dev/null || echo 0' | tr -d '[:space:]')"
echo "Baseline Athena SID alerts: $baseline"

if [[ "$SKIP_PROBE" != "1" ]]; then
  if ! curl -sf -o /dev/null --connect-timeout 3 "http://127.0.0.1:${JUICE_PORT}/"; then
    echo "Juice Shop not on host :${JUICE_PORT}." >&2
    echo "Start with: docker run -d --name juice-shop.lab -p ${JUICE_PORT}:3000 bkimminich/juice-shop:latest" >&2
    exit 1
  fi
  title="$(curl -sf "http://127.0.0.1:${JUICE_PORT}/" | python3 -c 'import sys,re; m=re.search(r"<title>([^<]+)", sys.stdin.read()); print(m.group(1) if m else "?")' 2>/dev/null || echo "?")"
  echo "Host title: $title"
  if ! echo "$title" | grep -qi juice; then
    echo "WARNING: :${JUICE_PORT} does not look like Juice Shop (got: $title)" >&2
  fi

  SCENARIO_ID="$(uuidgen | tr '[:upper:]' '[:lower:]')"
  RUN_ID="run-$(uuidgen | tr '[:upper:]' '[:lower:]' | cut -c1-8)"
  : >"$GT_OUTPUT"

  echo "Scenario: $SCENARIO_LABEL id=$SCENARIO_ID run=$RUN_ID"

  kubectl -n "$NS" create configmap day21-sqli-probe-script \
    --from-file=probe.sh="$ROOT/scripts/day21-sqli-probe.sh" \
    --dry-run=client -o yaml | kubectl apply -f -

  kubectl -n "$NS" delete job day21-sqli-probe --ignore-not-found >/dev/null 2>&1 || true
  cat <<EOF | kubectl -n "$NS" apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: day21-sqli-probe
  labels:
    app.kubernetes.io/name: day21-sqli-probe
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
              readOnly: true
      volumes:
        - name: script
          configMap:
            name: day21-sqli-probe-script
            defaultMode: 0755
EOF

  kubectl -n "$NS" wait --for=condition=complete job/day21-sqli-probe --timeout=120s || {
    echo "Job did not complete; dumping logs:" >&2
    kubectl -n "$NS" logs job/day21-sqli-probe || true
    exit 1
  }
  kubectl -n "$NS" logs job/day21-sqli-probe

  python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

sid, rid, label = "$SCENARIO_ID", "$RUN_ID", "$SCENARIO_LABEL"
target = "${JUICE_HOST}:${JUICE_PORT}"
rows = [
    ("observe", f"Juice Shop reachable via {target}", "benign_control", ""),
    ("plan", "Selected URI SQLi + login SQLi (T1190)", "benign_control", ""),
    ("act", "GET /rest/products/search?q=' OR 1=1--", "malicious", "http-request"),
    ("act", "POST /rest/user/login email=' OR 1=1--", "malicious", "http-request"),
    ("act", "GET /rest/products/search?q=qwert')", "malicious", "http-request"),
    ("reflect", "SQLi probes sent on vznat path for Suricata observation", "successful_simulation", ""),
]
path = Path("$GT_OUTPUT")
with path.open("w", encoding="utf-8") as fh:
    for phase, summary, lab, tool in rows:
        row = {
            "timestamp": now(),
            "phase": phase,
            "scenario_id": sid,
            "run_id": rid,
            "target": target,
            "summary": summary,
            "technique": "T1190",
            "label": lab,
            "scenario_label": label,
        }
        if tool:
            row["tool"] = tool
        fh.write(json.dumps(row, separators=(",", ":")) + "\n")
print(f"Wrote {len(rows)} GT events → {path}")
PY
fi

echo ""
echo "== Suricata eve.json (Athena SIDs 20261601–203) =="
sleep 3
: >"$ALERTS_OUT"
kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep "\"signature_id\":2026160" /var/log/suricata/eve.json 2>/dev/null | tail -80' \
  | tee "$ALERTS_OUT" || true

after="$(kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep -c "\"signature_id\":2026160" /var/log/suricata/eve.json 2>/dev/null || echo 0' | tr -d '[:space:]')"
echo ""
echo "Athena SID alerts: baseline=$baseline after=$after"
python3 - <<PY
import json, collections
from pathlib import Path
p = Path("$ALERTS_OUT")
counts = collections.Counter()
ifaces = collections.Counter()
msgs = collections.Counter()
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
    ifaces[ev.get("in_iface")] += 1
    msgs[alert.get("signature")] += 1
print("SID counts:", dict(counts))
print("signatures:", dict(msgs))
print("ifaces:", dict(ifaces))
PY
echo "GT: $GT_OUTPUT"
echo "Alerts extract: $ALERTS_OUT"
