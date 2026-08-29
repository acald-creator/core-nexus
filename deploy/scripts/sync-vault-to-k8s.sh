#!/usr/bin/env bash
# Pull secrets from an *external* Vault (nexus-hashistack locally) into Kubernetes:
#   wazuh-secrets          ← secret/soc/wazuh
#   nexus-gateway-secrets  ← secret/soc/wazuh + secret/nexus/dev|prod (+ optional AppRole env)
#
# Prerequisites:
#   cd ../nexus-hashistack && ./scripts/nexus-dev-up.sh
#   kubectl context pointing at the target cluster
#
# Optional AppRole injection (from hashistack export):
#   source ../nexus-hashistack/.approle/gateway.env   # sets VAULT_ROLE_ID / VAULT_SECRET_ID
#   ./deploy/scripts/sync-vault-to-k8s.sh
#
# R2 / non-lab gateway credentials:
#   NEXUS_VAULT_GW_PATH=nexus/prod ./deploy/scripts/sync-vault-to-k8s.sh
#   (default path is nexus/dev — lab MinIO keys)
set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-myroot}"
NAMESPACE="${NAMESPACE:-soc}"
INDEXER_USERNAME="${INDEXER_USERNAME:-admin}"
WAZUH_API_USER="${WAZUH_API_USER:-wazuh-wui}"
# KV path under secret/data/ — lab MinIO (nexus/dev) or R2 (nexus/prod)
NEXUS_VAULT_GW_PATH="${NEXUS_VAULT_GW_PATH:-nexus/dev}"

echo "Syncing secrets from HashiCorp Vault to Kubernetes..."
echo "Vault Address: ${VAULT_ADDR}"
echo "K8s Namespace: ${NAMESPACE}"
echo "Gateway KV:    secret/${NEXUS_VAULT_GW_PATH}"

kv_get() {
  local path="$1"
  curl -s -w "\n%{http_code}" \
    --header "X-Vault-Token: ${VAULT_TOKEN}" \
    "${VAULT_ADDR}/v1/secret/data/${path}"
}

parse_body() {
  local raw="$1"
  echo "$raw" | sed '$d'
}

parse_status() {
  local raw="$1"
  echo "$raw" | tail -n1
}

SOC_RAW="$(kv_get soc/wazuh)"
SOC_STATUS="$(parse_status "$SOC_RAW")"
SOC_BODY="$(parse_body "$SOC_RAW")"
if [ "$SOC_STATUS" -ne 200 ]; then
  echo "ERROR: Failed to read secret/soc/wazuh (HTTP $SOC_STATUS)" >&2
  echo "$SOC_BODY" >&2
  exit 1
fi

GW_RAW="$(kv_get "${NEXUS_VAULT_GW_PATH}")"
GW_STATUS="$(parse_status "$GW_RAW")"
GW_BODY="$(parse_body "$GW_RAW")"
if [ "$GW_STATUS" -ne 200 ]; then
  echo "ERROR: Failed to read secret/${NEXUS_VAULT_GW_PATH} (HTTP $GW_STATUS)" >&2
  echo "$GW_BODY" >&2
  exit 1
fi

eval "$(python3 - "$SOC_BODY" "$GW_BODY" "${NEXUS_VAULT_GW_PATH}" <<'PY'
import json, sys, shlex
soc = json.loads(sys.argv[1])["data"]["data"]
gw = json.loads(sys.argv[2])["data"]["data"]
path = sys.argv[3]
lab = path.rstrip("/") == "nexus/dev"
pairs = {
    "INDEXER_PASS": soc.get("OPENSEARCH_INITIAL_ADMIN_PASSWORD", ""),
    "API_PASS": soc.get("WAZUH_API_PASSWORD", ""),
    "JWT_SECRET": gw.get(
        "NEXUS_GW_JWT_SECRET",
        "dev-secret-do-not-use-in-production" if lab else "",
    ),
    "MINIO_AK": gw.get(
        "NEXUS_GW_MINIO_ACCESS_KEY",
        "minioadmin" if lab else "",
    ),
    "MINIO_SK": gw.get(
        "NEXUS_GW_MINIO_SECRET_KEY",
        "minioadmin" if lab else "",
    ),
}
for k, v in pairs.items():
    print(f"{k}={shlex.quote(str(v))}")
PY
)"

if [ -z "${INDEXER_PASS}" ] || [ -z "${API_PASS}" ]; then
  echo "ERROR: soc/wazuh passwords empty." >&2
  exit 1
fi

if [ -z "${JWT_SECRET}" ] || [ -z "${MINIO_AK}" ] || [ -z "${MINIO_SK}" ]; then
  echo "ERROR: secret/${NEXUS_VAULT_GW_PATH} missing JWT or object-store keys." >&2
  echo "  For R2: seed secret/nexus/prod (see overlays/r2/README.md)." >&2
  exit 1
fi

ROLE_ID="${VAULT_ROLE_ID:-${NEXUS_GW_VAULT_ROLE_ID:-}}"
SECRET_ID="${VAULT_SECRET_ID:-${NEXUS_GW_VAULT_SECRET_ID:-}}"

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

echo "Updating Secret wazuh-secrets..."
kubectl create secret generic wazuh-secrets \
  --namespace="${NAMESPACE}" \
  --from-literal=OPENSEARCH_INITIAL_ADMIN_PASSWORD="${INDEXER_PASS}" \
  --from-literal=WAZUH_API_PASSWORD="${API_PASS}" \
  --from-literal=INDEXER_USERNAME="${INDEXER_USERNAME}" \
  --from-literal=WAZUH_API_USER="${WAZUH_API_USER}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Updating Secret nexus-gateway-secrets..."
GW_ARGS=(
  --namespace="${NAMESPACE}"
  --from-literal=NEXUS_GW_JWT_SECRET="${JWT_SECRET}"
  --from-literal=NEXUS_GW_MINIO_ACCESS_KEY="${MINIO_AK}"
  --from-literal=NEXUS_GW_MINIO_SECRET_KEY="${MINIO_SK}"
  --from-literal=NEXUS_GW_WAZUH_API_PASSWORD="${API_PASS}"
  --from-literal=NEXUS_GW_VAULT_ROLE_ID="${ROLE_ID}"
  --from-literal=NEXUS_GW_VAULT_SECRET_ID="${SECRET_ID}"
)
kubectl create secret generic nexus-gateway-secrets \
  "${GW_ARGS[@]}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "SUCCESS: wazuh-secrets + nexus-gateway-secrets synced."
echo "  kubectl rollout restart deployment/nexus-api-gateway deployment/wazuh-manager -n ${NAMESPACE}"
