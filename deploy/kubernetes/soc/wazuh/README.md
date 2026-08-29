# Wazuh (manager + indexer) for SOC labs

Credentials are **not** hardcoded on the Deployments. They come from Secret
`wazuh-secrets`:

| Key | Used by |
|-----|---------|
| `OPENSEARCH_INITIAL_ADMIN_PASSWORD` | Indexer admin + manager `INDEXER_PASSWORD` |
| `WAZUH_API_PASSWORD` | Manager API (`API_PASSWORD` / `WAZUH_API_PASSWORD`) |
| `INDEXER_USERNAME` | Manager → indexer (default `admin`) |
| `WAZUH_API_USER` | Manager API user (default `wazuh-wui`) |

## Apply

```bash
# Placeholder secret (changeme) is included in this kustomize
kubectl apply -k deploy/kubernetes/soc/wazuh

# Preferred: overwrite from nexus-hashistack Vault
cd ../nexus-hashistack && ./scripts/nexus-dev-up.sh
cd ../core-nexus
./deploy/scripts/sync-vault-to-k8s.sh
kubectl rollout restart deployment/wazuh-manager -n soc
```

Point the API Gateway at the manager:

```bash
NEXUS_GW_WAZUH_API_URL=https://wazuh-manager.soc.svc.cluster.local:55000
NEXUS_GW_WAZUH_API_PASSWORD=<same as Vault WAZUH_API_PASSWORD>
```

## Security note

`DISABLE_SECURITY_PLUGIN=true` keeps the indexer on HTTP for this lab scaffold.
Do not promote that setting to staging/prod; enable OpenSearch security + TLS
and keep using the same Secret keys via Vault sync / External Secrets.
