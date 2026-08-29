# SOC Kubernetes overlays

Workloads live here: **API Gateway**, **Console**, AI, MCP, Jupyter workbench,
Athena, MinIO (lab), optional Wazuh. Suricata is under `deploy/kubernetes/system/suricata`
(see `overlays/test`). Desktop webtops are **not** part of this tree.

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
| `nexus-gateway-secrets` | Vault `secret/nexus/dev` (lab) or `secret/nexus/prod` (R2) + wazuh password (+ optional AppRole ids) |

```bash
# After Vault is up — also picks up VAULT_ROLE_ID/SECRET_ID if exported in the shell
source ../nexus-hashistack/.approle/gateway.env 2>/dev/null || true
./deploy/scripts/sync-vault-to-k8s.sh
# R2 overlay:
# NEXUS_VAULT_GW_PATH=nexus/prod ./deploy/scripts/sync-vault-to-k8s.sh
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
| `overlays/gitops-lab` | Thin Console + gateway; Flux image pins (MinIO-era) |
| `overlays/r2` | Console + gateway on Cloudflare R2 (Argo `nexus-gitops-lab`) |
| `overlays/gitops-range` | Jupyter workbench + Athena standard (Argo `nexus-gitops-range`) |
| `overlays/wazuh-secure` | Wazuh only with TLS/security indexer |
| `overlays/test` | System charts + Wazuh secure component (needs Helm) |
| `overlays/prod` | Helm MinIO; Vault stays external |

**Retired:** `nexus-webtop-soc` / `nexus-webtop-workbench` desktops — do not re-add the
webtop-soc Git remote to `base/`. Suricata: `deploy/kubernetes/system/suricata`.
