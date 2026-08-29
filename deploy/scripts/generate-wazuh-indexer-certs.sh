#!/usr/bin/env bash
# Generate lab TLS material for Wazuh/OpenSearch indexer and load into Kubernetes.
#
# Creates Secret wazuh-indexer-certs in NAMESPACE (default: soc) with:
#   root-ca.pem, node.pem, node-key.pem, admin.pem, admin-key.pem
#
# Usage:
#   ./deploy/scripts/generate-wazuh-indexer-certs.sh
#   NAMESPACE=soc ./deploy/scripts/generate-wazuh-indexer-certs.sh
#
# Then apply the secure test overlay (or wazuh + secure patches).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NAMESPACE="${NAMESPACE:-soc}"
OUT="${WAZUH_CERT_DIR:-$REPO_ROOT/deploy/kubernetes/soc/wazuh/.certs}"
DAYS="${CERT_DAYS:-825}"

mkdir -p "$OUT"
chmod 700 "$OUT"

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required" >&2
  exit 1
fi

echo "Generating lab CA + node/admin certs in $OUT ..."

# Root CA
openssl req -x509 -newkey rsa:4096 -sha256 -days "$DAYS" -nodes \
  -keyout "$OUT/root-ca-key.pem" \
  -out "$OUT/root-ca.pem" \
  -subj "/C=US/O=UndergroundNexus/OU=SOC/CN=wazuh-lab-ca" 2>/dev/null

# Node (indexer) cert
openssl req -newkey rsa:2048 -nodes \
  -keyout "$OUT/node-key.pem" \
  -out "$OUT/node.csr" \
  -subj "/C=US/O=UndergroundNexus/OU=SOC/CN=wazuh-indexer" 2>/dev/null

cat >"$OUT/node.ext" <<EOF
subjectAltName=DNS:wazuh-indexer,DNS:wazuh-indexer.soc.svc,DNS:wazuh-indexer.soc.svc.cluster.local,DNS:localhost,IP:127.0.0.1
extendedKeyUsage=serverAuth,clientAuth
EOF

openssl x509 -req -in "$OUT/node.csr" -CA "$OUT/root-ca.pem" -CAkey "$OUT/root-ca-key.pem" \
  -CAcreateserial -out "$OUT/node.pem" -days "$DAYS" -sha256 -extfile "$OUT/node.ext" 2>/dev/null

# Admin cert (security plugin admin DN)
openssl req -newkey rsa:2048 -nodes \
  -keyout "$OUT/admin-key.pem" \
  -out "$OUT/admin.csr" \
  -subj "/C=US/O=UndergroundNexus/OU=SOC/CN=admin" 2>/dev/null

openssl x509 -req -in "$OUT/admin.csr" -CA "$OUT/root-ca.pem" -CAkey "$OUT/root-ca-key.pem" \
  -CAcreateserial -out "$OUT/admin.pem" -days "$DAYS" -sha256 2>/dev/null

rm -f "$OUT"/*.csr "$OUT"/*.ext "$OUT"/*.srl

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

kubectl create secret generic wazuh-indexer-certs \
  --namespace="${NAMESPACE}" \
  --from-file=root-ca.pem="$OUT/root-ca.pem" \
  --from-file=node.pem="$OUT/node.pem" \
  --from-file=node-key.pem="$OUT/node-key.pem" \
  --from-file=admin.pem="$OUT/admin.pem" \
  --from-file=admin-key.pem="$OUT/admin-key.pem" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "SUCCESS: Secret wazuh-indexer-certs updated in namespace ${NAMESPACE}"
echo "  Local copies (gitignored): $OUT"
echo "  Next: kubectl apply -k deploy/kubernetes/soc/overlays/wazuh-secure"
