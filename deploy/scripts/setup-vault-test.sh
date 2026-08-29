#!/bin/sh
# Deprecated: in-cluster Vault init/unseal was removed from core-nexus.
#
# Shamir / file-backend labs live in nexus-hashistack:
#   cd ../nexus-hashistack
#   ./scripts/test-vault-up.sh
#   ./scripts/test-vault-smoke.sh

echo "setup-vault-test.sh is retired." >&2
echo "Use nexus-hashistack recipe 04 (Shamir test Vault):" >&2
echo "  cd ../nexus-hashistack && ./scripts/test-vault-up.sh" >&2
exit 1
