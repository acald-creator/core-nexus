# Overlay: R2 object store (non-lab)

Console + API gateway with **Cloudflare R2** for blobs. Lab MinIO stays the
default on `overlays/dev`, `overlays/gitops-lab`, and compose.

## Prerequisites

1. R2 bucket (e.g. `nexus-memory`) and an S3 API token (access key id + secret).
2. Cloudflare account id and a browser-reachable public host (custom domain or
   `*.r2.dev`).
3. Vault path for gateway credentials (hashistack seed supports this):

```bash
# From nexus-hashistack — only writes when R2 env vars are set
export NEXUS_GW_R2_ACCOUNT_ID=...
export NEXUS_GW_MINIO_ACCESS_KEY=...   # R2 access key id
export NEXUS_GW_MINIO_SECRET_KEY=...   # R2 secret access key
export NEXUS_GW_JWT_SECRET=...         # non-lab JWT
./scripts/seed-nexus-secrets.sh
```

Or put keys manually:

```bash
vault kv put secret/nexus/prod \
  NEXUS_GW_JWT_SECRET='...' \
  NEXUS_GW_MINIO_ACCESS_KEY='...' \
  NEXUS_GW_MINIO_SECRET_KEY='...'
```

## Apply

```bash
# Edit ConfigMap placeholders
$EDITOR deploy/kubernetes/soc/overlays/r2/object-store-config.yaml

# Sync secrets from Vault prod path (not nexus/dev lab MinIO keys)
NEXUS_VAULT_GW_PATH=nexus/prod ./deploy/scripts/sync-vault-to-k8s.sh

kubectl apply -k deploy/kubernetes/soc/overlays/r2
kubectl -n soc rollout restart deployment/nexus-api-gateway
```

Gateway env after patch: `NEXUS_GW_OBJECT_STORE_BACKEND=r2`, TLS on,
region `auto`, credentials from `nexus-gateway-secrets` (same key names as MinIO).

See `platform/api-gateway/OBJECT_STORE.md`.

## Full spine

This overlay uses the thin `console/` slice (no in-cluster MinIO). To attach the
same R2 patches to `base` (AI/MCP/Athena), copy the ConfigMap + gateway patch
and delete MinIO StatefulSet/Service as in `overlays/prod`.
