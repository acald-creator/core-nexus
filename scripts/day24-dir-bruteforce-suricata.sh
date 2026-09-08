#!/usr/bin/env bash
# Day 24 Use: run Athena dir-bruteforce traffic and verify Suricata catches it.
#
# 1) Local tool invoke against Juice Shop :3003 (real dir_bruteforce.py)
# 2) In-cluster labeled GET storm (same UA/paths) so Suricata multi-iface sees packets
# 3) Assert SIDs 20262401–203 (+ Athena labels 20261601–602)
#
# Usage:
#   ./scripts/day24-dir-bruteforce-suricata.sh
#   ./scripts/day24-dir-bruteforce-suricata.sh --skip-apply
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ATHENA_AGENTS="${ATHENA_AGENTS:-$(cd "$ROOT/../athena-agents" 2>/dev/null && pwd || true)}"
SKIP_APPLY=0
NS="${DAY24_NS:-soc}"
ALERTS_OUT="${DAY24_ALERTS_OUT:-/tmp/day24-suricata-alerts.jsonl}"
GT_OUTPUT="${ATHENA_GT_OUTPUT:-/tmp/day24-gt.jsonl}"
JUICE_PORT="${JUICE_PORT:-3003}"
JUICE_HOST="${JUICE_HOST:-host.docker.internal}"
JUICE_BASE="http://${JUICE_HOST}:${JUICE_PORT}"

for arg in "$@"; do
  case "$arg" in
    --skip-apply) SKIP_APPLY=1 ;;
  esac
done

echo "== Day 24: dir-bruteforce → Suricata =="

if [[ "$SKIP_APPLY" != "1" ]]; then
  echo "Applying Suricata ConfigMap + DaemonSet..."
  kubectl apply -k "$ROOT/deploy/kubernetes/system/suricata" -n "$NS"
  kubectl -n "$NS" rollout restart daemonset/suricata
  kubectl -n "$NS" rollout status daemonset/suricata --timeout=180s
  echo "Waiting for Suricata engine settle..."
  sleep 25
fi

SURICATA_POD="$(kubectl -n "$NS" get pod -l app.kubernetes.io/name=suricata -o jsonpath='{.items[0].metadata.name}')"
echo "Suricata pod: $SURICATA_POD"
kubectl -n "$NS" exec "$SURICATA_POD" -c suricata -- grep -E "sid:2026240" /etc/suricata/athena.rules

if ! curl -sf -o /dev/null --connect-timeout 3 "http://127.0.0.1:${JUICE_PORT}/"; then
  echo "Juice Shop not on host :${JUICE_PORT}" >&2
  exit 1
fi

# --- Local real tool (host path; Suricata may not see this) ---
if [[ -n "${ATHENA_AGENTS}" && -d "${ATHENA_AGENTS}/orchestrator/tools" ]]; then
  echo ""
  echo "== Local dir_bruteforce.py against 127.0.0.1:${JUICE_PORT} =="
  PYTHON="${ATHENA_AGENTS}/.venv/bin/python"
  [[ -x "$PYTHON" ]] || PYTHON=python3
  "$PYTHON" - <<PY
import asyncio, json, sys
sys.path.insert(0, "${ATHENA_AGENTS}")
from orchestrator.allowlist import AllowlistEntry
from orchestrator.tools import dir_bruteforce

async def main():
    result = await dir_bruteforce.run(
        {
            "target": "127.0.0.1",
            "port": ${JUICE_PORT},
            "max_entries": 23,
            "concurrency": 4,
            "wordlist": "${ATHENA_AGENTS}/config/wordlists/common-dirs.txt",
        },
        default_target="127.0.0.1",
        default_port=${JUICE_PORT},
        allowlist=[
            AllowlistEntry(
                host="127.0.0.1",
                port_range=(${JUICE_PORT}, ${JUICE_PORT}),
                protocol="http",
                label="juice-shop-day24",
            )
        ],
        headers={
            "X-Athena-Scenario": "juice-shop-dirbrute",
            "X-Athena-Scenario-Id": "day24-local",
            "X-Athena-Run-ID": "run-local",
        },
    )
    print(json.dumps(result.output, indent=2))
    if not result.success:
        raise SystemExit(result.error or "dir-bruteforce failed")
    print(f"LOCAL_OK probed={result.output.get('probed')} hits={result.output.get('hit_count')}")

asyncio.run(main())
PY
else
  echo "WARN: athena-agents not found at ${ATHENA_AGENTS:-?}; skipping local tool invoke" >&2
fi

baseline="$(kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep -c "\"signature_id\":2026240" /var/log/suricata/eve.json 2>/dev/null || echo 0' | tr -d '[:space:]' | sed 's/00$/0/;s/^0\([0-9]\)/\1/')"
# Normalize busybox grep -c 0 || echo 0 → "00"
baseline="$(echo "$baseline" | grep -oE '[0-9]+' | tail -1)"
echo "Baseline Day 24 SID alerts: $baseline"

SCENARIO_ID="$(uuidgen | tr '[:upper:]' '[:lower:]')"
RUN_ID="run-$(uuidgen | tr '[:upper:]' '[:lower:]' | cut -c1-8)"
SCENARIO_LABEL="juice-shop-dirbrute"
: >"$GT_OUTPUT"

echo ""
echo "== In-cluster probe (Suricata capture path) =="
echo "Target: $JUICE_BASE scenario=$SCENARIO_LABEL id=$SCENARIO_ID"

kubectl -n "$NS" create configmap day24-dirbrute-probe-script \
  --from-file=probe.sh="$ROOT/scripts/day24-dirbrute-probe.sh" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "$NS" delete job day24-dirbrute-probe --ignore-not-found >/dev/null 2>&1 || true
cat <<EOF | kubectl -n "$NS" apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: day24-dirbrute-probe
  labels:
    app.kubernetes.io/name: day24-dirbrute-probe
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
            name: day24-dirbrute-probe-script
            defaultMode: 0755
EOF

kubectl -n "$NS" wait --for=condition=complete job/day24-dirbrute-probe --timeout=120s || {
  kubectl -n "$NS" logs job/day24-dirbrute-probe || true
  exit 1
}
kubectl -n "$NS" logs job/day24-dirbrute-probe

python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

sid, rid, label = "$SCENARIO_ID", "$RUN_ID", "$SCENARIO_LABEL"
rows = [
    ("observe", "Juice Shop :${JUICE_PORT} reachable", "benign_control", ""),
    ("plan", "Selected dir-bruteforce wordlist scan (T1595)", "benign_control", ""),
    ("act", "dir-bruteforce common-dirs against Juice Shop", "malicious", "dir-bruteforce"),
    ("reflect", "Labeled GET storm for Suricata Day 24 observation", "successful_simulation", ""),
]
path = Path("$GT_OUTPUT")
with path.open("w", encoding="utf-8") as fh:
    for phase, summary, lab, tool in rows:
        row = {
            "timestamp": now(),
            "phase": phase,
            "scenario_id": sid,
            "run_id": rid,
            "target": "${JUICE_HOST}:${JUICE_PORT}",
            "summary": summary,
            "technique": "T1595",
            "label": lab,
            "scenario_label": label,
        }
        if tool:
            row["tool"] = tool
        fh.write(json.dumps(row, separators=(",", ":")) + "\n")
print(f"Wrote {len(rows)} GT events → {path}")
PY

echo ""
echo "== Suricata eve.json (SIDs 20262401–203) =="
sleep 3
: >"$ALERTS_OUT"
kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep "\"signature_id\":2026240" /var/log/suricata/eve.json 2>/dev/null | tail -120' \
  | tee "$ALERTS_OUT" || true

after="$(kubectl -n "$NS" exec "$SURICATA_POD" -c log-tail -- sh -c \
  'grep -c "\"signature_id\":2026240" /var/log/suricata/eve.json 2>/dev/null || echo 0' | tr -d '[:space:]')"
after="$(echo "$after" | grep -oE '[0-9]+' | tail -1)"
echo "Day 24 SID alerts: baseline=$baseline after=$after"

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
needed = {20262401, 20262402, 20262403}
missing = needed - set(counts)
if missing:
    print(f"FAIL: missing SIDs {sorted(missing)}", file=sys.stderr)
    sys.exit(1)
print("OK: all three Day 24 SIDs fired")
PY

echo "Alerts extract: $ALERTS_OUT"
echo "GT: $GT_OUTPUT"
