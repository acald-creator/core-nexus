#!/usr/bin/env bash
# Pull secret/soc/wazuh from an *external* Vault (nexus-hashistack locally)
# into Kubernetes Secret wazuh-secrets (consumed by deploy/kubernetes/soc/wazuh).
#
# Prerequisites:
#   cd ../nexus-hashistack && ./scripts/nexus-dev-up.sh
#   kubectl context pointing at the target cluster / namespace
#
# Defaults match the local HashiStack lab token and seed paths.
set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-myroot}"
NAMESPACE="${NAMESPACE:-soc}"
INDEXER_USERNAME="${INDEXER_USERNAME:-admin}"
WAZUH_API_USER="${WAZUH_API_USER:-wazuh-wui}"

echo "Syncing secrets from HashiCorp Vault to Kubernetes..."
echo "Vault Address: ${VAULT_ADDR}"
echo "K8s Namespace: ${NAMESPACE}"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  --header "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/secret/data/soc/wazuh")

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_STATUS" -ne 200 ]; then
  echo "ERROR: Failed to retrieve secrets from Vault. HTTP Status: $HTTP_STATUS" >&2
  echo "Response Body: $BODY" >&2
  exit 1
fi

INDEXER_PASS=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['data'].get('OPENSEARCH_INITIAL_ADMIN_PASSWORD', ''))")
API_PASS=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['data'].get('WAZUH_API_PASSWORD', ''))")

if [ -z "$INDEXER_PASS" ] || [ -z "$API_PASS" ]; then
  echo "ERROR: Retrieved secrets are empty or could not be parsed." >&2
  exit 1
fi

echo "Creating/updating Kubernetes Secret 'wazuh-secrets' in namespace '${NAMESPACE}'..."
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl create secret generic wazuh-secrets \
  --namespace="${NAMESPACE}" \
  --from-literal=OPENSEARCH_INITIAL_ADMIN_PASSWORD="${INDEXER_PASS}" \
  --from-literal=WAZUH_API_PASSWORD="${API_PASS}" \
  --from-literal=INDEXER_USERNAME="${INDEXER_USERNAME}" \
  --from-literal=WAZUH_API_USER="${WAZUH_API_USER}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "SUCCESS: wazuh-secrets synced (indexer + API passwords)."
echo "  Restart manager if it was already running:"
echo "    kubectl rollout restart deployment/wazuh-manager -n ${NAMESPACE}"
