# SOC Kubernetes overlays

Workloads (AI, MCP, workbench, Athena, MinIO, webtop-soc) live here.

**Vault is not deployed from this tree.** Local and lab Vault come from the sibling
[nexus-hashistack](https://github.com/acald-creator/nexus-hashistack) repo:

```bash
cd ../nexus-hashistack
./scripts/nexus-dev-up.sh              # Dev Vault :8200
./scripts/test-vault-up.sh             # Shamir / file lab (recipe 04)
```

Point apps at that Vault (`VAULT_ADDR`, AppRole export, or future ESO/injector).
Optional: `./deploy/scripts/sync-vault-to-k8s.sh` overwrites Secret `wazuh-secrets`
from Vault `secret/soc/wazuh` (see `deploy/kubernetes/soc/wazuh/README.md`).

| Overlay | Role |
|---------|------|
| `base` | Shared Deployments (no Vault); images `phoenixvlabs/nexus-*` |
| `overlays/dev` | Disposable lab (same base) |
| `overlays/test` | Adds system charts + Wazuh |
| `overlays/prod` | Helm MinIO; Vault stays external |
