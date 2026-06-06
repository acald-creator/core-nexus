#!/bin/sh

# Default Vault location and dev token
VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-myroot}"

echo "Initializing secrets in HashiCorp Vault..."
echo "Vault Address: ${VAULT_ADDR}"

# Payload structure for kv-v2
PAYLOAD='{
  "data": {
    "OPENSEARCH_INITIAL_ADMIN_PASSWORD": "admin",
    "WAZUH_API_PASSWORD": "admin"
  }
}'

# Write the secrets using curl
RESPONSE=$(curl -s -w "\n%{http_code}" \
  --header "X-Vault-Token: ${VAULT_TOKEN}" \
  --header "Content-Type: application/json" \
  --request POST \
  --data "$PAYLOAD" \
  "${VAULT_ADDR}/v1/secret/data/soc/wazuh")

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 204 ]; then
  echo "SUCCESS: Secrets initialized successfully in Vault at 'secret/soc/wazuh'."
else
  echo "ERROR: Failed to write secrets to Vault. HTTP Status: $HTTP_STATUS"
  echo "Response Body: $BODY"
  exit 1
fi
