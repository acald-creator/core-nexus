# Wazuh (manager + indexer) for SOC labs

Credentials are **not** hardcoded on the Deployments. They come from Secret
`wazuh-secrets`:

| Key | Used by |
|-----|---------|
| `OPENSEARCH_INITIAL_ADMIN_PASSWORD` | Indexer admin + manager `INDEXER_PASSWORD` |
| `WAZUH_API_PASSWORD` | Manager API (`API_PASSWORD` / `WAZUH_API_PASSWORD`) |
| `INDEXER_USERNAME` | Manager → indexer (default `admin`) |
| `WAZUH_API_USER` | Manager API user (default `wazuh-wui`) |

## Profiles

| Profile | Indexer | Apply |
|---------|---------|-------|
| **HTTP lab** | Security plugin off | `kubectl apply -k deploy/kubernetes/soc/wazuh` |
| **TLS lab** | Security + TLS | `kubectl apply -k deploy/kubernetes/soc/overlays/wazuh-secure` |

## Apply (HTTP lab)

```bash
kubectl apply -k deploy/kubernetes/soc/wazuh
cd ../nexus-hashistack && ./scripts/nexus-dev-up.sh
cd ../core-nexus && ./deploy/scripts/sync-vault-to-k8s.sh
kubectl rollout restart deployment/wazuh-manager -n soc
```

## Apply (TLS / security)

```bash
./deploy/scripts/generate-wazuh-indexer-certs.sh   # Secret wazuh-indexer-certs
./deploy/scripts/sync-vault-to-k8s.sh
kubectl apply -k deploy/kubernetes/soc/overlays/wazuh-secure
kubectl rollout restart deployment/wazuh-indexer deployment/wazuh-manager -n soc
```

Manager uses `INDEXER_URL=https://wazuh-indexer:9200` with
`FILEBEAT_SSL_VERIFICATION_MODE=none` for this lab. Replace with proper CA trust
before production. The full `overlays/test` stack also includes this secure
component (plus system charts that need Helm).

Point the API Gateway at the manager:

```bash
NEXUS_GW_WAZUH_API_URL=https://wazuh-manager.soc.svc.cluster.local:55000
NEXUS_GW_WAZUH_API_PASSWORD=<same as Vault WAZUH_API_PASSWORD>
```
