#!/bin/bash
set -e

NAMESPACE="soc"
VAULT_POD=$(kubectl get pod -n ${NAMESPACE} -l app=vault -o jsonpath="{.items[0].metadata.name}" 2>/dev/null || true)

if [ -z "$VAULT_POD" ]; then
    echo "Vault pod not found in namespace ${NAMESPACE}."
    exit 1
fi

echo "Found Vault pod: ${VAULT_POD}"

# Check if initialized
INIT_STATUS=$(kubectl exec -n ${NAMESPACE} ${VAULT_POD} -- env VAULT_ADDR=http://127.0.0.1:8200 vault status -format=json 2>/dev/null | jq -r '.initialized' || true)

KEYS_FILE="deploy/kubernetes/soc/overlays/test/cluster-keys.json"

if [ "$INIT_STATUS" != "true" ]; then
    echo "Vault is not initialized. Initializing now..."
    # Initialize with 1 key share and 1 key threshold for test convenience
    kubectl exec -n ${NAMESPACE} ${VAULT_POD} -- env VAULT_ADDR=http://127.0.0.1:8200 vault operator init -key-shares=1 -key-threshold=1 -format=json > "${KEYS_FILE}"
    echo "Vault initialized. Keys saved to ${KEYS_FILE}"
    echo "WARNING: ${KEYS_FILE} contains highly sensitive credentials. Do not commit this file to git!"
else
    echo "Vault is already initialized."
fi

if [ ! -f "${KEYS_FILE}" ]; then
    echo "Error: ${KEYS_FILE} not found. Cannot unseal Vault without keys."
    exit 1
fi

# Extract keys
UNSEAL_KEY=$(jq -r '.unseal_keys_b64[0]' "${KEYS_FILE}")
ROOT_TOKEN=$(jq -r '.root_token' "${KEYS_FILE}")

# Check if sealed
SEAL_STATUS=$(kubectl exec -n ${NAMESPACE} ${VAULT_POD} -- env VAULT_ADDR=http://127.0.0.1:8200 vault status -format=json 2>/dev/null | jq -r '.sealed' || true)

if [ "$SEAL_STATUS" == "true" ]; then
    echo "Vault is sealed. Unsealing now..."
    kubectl exec -n ${NAMESPACE} ${VAULT_POD} -- env VAULT_ADDR=http://127.0.0.1:8200 vault operator unseal "${UNSEAL_KEY}" > /dev/null
    echo "Vault successfully unsealed."
else
    echo "Vault is already unsealed."
fi

echo ""
echo "You can now interact with the test Vault using the root token:"
echo "export VAULT_TOKEN=${ROOT_TOKEN}"
echo "export VAULT_ADDR=http://127.0.0.1:8200"
echo ""
echo "To port-forward the Vault UI to localhost:"
echo "kubectl port-forward -n ${NAMESPACE} svc/vault 8200:8200"
