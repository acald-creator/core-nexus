#!/bin/sh
# Deprecated: Vault seeding lives in nexus-hashistack.
#
#   cd ../nexus-hashistack
#   ./scripts/nexus-dev-up.sh
#   # seeds secret/soc/wazuh and secret/nexus/dev
#
# To push already-seeded secrets into Kubernetes, use:
#   ./deploy/scripts/sync-vault-to-k8s.sh
# (expects VAULT_ADDR pointing at hashistack or another external Vault)

echo "init-vault-secrets.sh is retired." >&2
echo "Seed Vault from nexus-hashistack:" >&2
echo "  cd ../nexus-hashistack && ./scripts/nexus-dev-up.sh" >&2
echo "Then optionally: ./deploy/scripts/sync-vault-to-k8s.sh" >&2
exit 1
