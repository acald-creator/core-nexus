#!/bin/sh

# Default Vault location, dev token, and namespace
VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-myroot}"
NAMESPACE="${NAMESPACE:-soc}"

echo "Syncing secrets from HashiCorp Vault to Kubernetes..."
echo "Vault Address: ${VAULT_ADDR}"
echo "K8s Namespace: ${NAMESPACE}"

# Retrieve the secrets from Vault
RESPONSE=$(curl -s -w "\n%{http_code}" \
  --header "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/secret/data/soc/wazuh")

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_STATUS" -ne 200 ]; then
  echo "ERROR: Failed to retrieve secrets from Vault. HTTP Status: $HTTP_STATUS"
  echo "Response Body: $BODY"
  exit 1
fi

# Parse credentials using Python (portable, no jq dependency required)
INDEXER_PASS=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['data'].get('OPENSEARCH_INITIAL_ADMIN_PASSWORD', ''))")
API_PASS=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['data'].get('WAZUH_API_PASSWORD', ''))")

if [ -z "$INDEXER_PASS" ] || [ -z "$API_PASS" ]; then
  echo "ERROR: Retrieved secrets are empty or could not be parsed."
  exit 1
fi

# Apply to Kubernetes
echo "Creating/updating Kubernetes Secret 'wazuh-secrets' in namespace '${NAMESPACE}'..."
kubectl create secret generic wazuh-secrets \
  --namespace="${NAMESPACE}" \
  --from-literal=OPENSEARCH_INITIAL_ADMIN_PASSWORD="${INDEXER_PASS}" \
  --from-literal=WAZUH_API_PASSWORD="${API_PASS}" \
  --dry-run=client -o yaml | kubectl apply -f -

if [ $? -eq 0 ]; then
  echo "SUCCESS: Kubernetes Secret 'wazuh-secrets' synced successfully."
else
  echo "ERROR: Failed to apply Kubernetes Secret."
  exit 1
fi
