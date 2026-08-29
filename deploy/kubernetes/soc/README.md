# SOC Kubernetes overlays

Workloads live here: **API Gateway**, **Console**, AI, MCP, workbench, Athena, MinIO,
optional Wazuh, and webtop-soc (remote base).

**Vault is not deployed from this tree.** Local and lab Vault come from
[nexus-hashistack](https://github.com/acald-creator/nexus-hashistack):

```bash
cd ../nexus-hashistack
./scripts/nexus-dev-up.sh
./scripts/admin-bootstrap-approle.sh   # optional AppRole for gateway hydrate
```

## Secrets

| Secret | Source |
|--------|--------|
| `wazuh-secrets` | Vault `secret/soc/wazuh` via `./deploy/scripts/sync-vault-to-k8s.sh` |
| `nexus-gateway-secrets` | Vault `secret/nexus/dev` + wazuh password (+ optional AppRole ids) |

```bash
# After Vault is up — also picks up VAULT_ROLE_ID/SECRET_ID if exported in the shell
source ../nexus-hashistack/.approle/gateway.env 2>/dev/null || true
./deploy/scripts/sync-vault-to-k8s.sh
```

## Apply (base spine)

```bash
kubectl apply -k deploy/kubernetes/soc/overlays/dev
# or: kubectl apply -k deploy/kubernetes/soc/base
kubectl rollout restart deployment/nexus-api-gateway -n soc
```

Port-forward for local browser:

```bash
kubectl -n soc port-forward svc/nexus-console 3000:80
kubectl -n soc port-forward svc/nexus-api-gateway 3100:3100
# Console image should be built with VITE_API_GATEWAY_URL=http://localhost:3100
```

| Overlay | Role |
|---------|------|
| `base` | Gateway, Console, AI, MCP, Athena, MinIO (images `phoenixvlabs/nexus-*`) |
| `overlays/dev` | Same base (disposable lab) |
| `overlays/test` | Adds system charts + Wazuh |
| `overlays/prod` | Helm MinIO; Vault stays external |
