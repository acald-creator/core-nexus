# Overlay: R2 object store (non-lab)

Console + API gateway with **Cloudflare R2** for blobs. Lab MinIO stays the
default on `overlays/dev`, `overlays/gitops-lab`, and compose.

## Prerequisites

**Already provisioned via wrangler (this account):**

| Item | Value |
|------|--------|
| Account ID | `901cf745bc4091a67a1070c2d0d61574` |
| Bucket | `nexus-memory` |
| S3 API host | `901cf745bc4091a67a1070c2d0d61574.r2.cloudflarestorage.com` |
| Anonymous `r2.dev` | `pub-4eedfccbd8d54c079ac8d5a969954953.r2.dev` (optional public objects) |
| CORS | `r2-cors.json` applied to the bucket |

ConfigMap `object-store-config.yaml` is filled with account id + S3 host.

**Still required — S3 API token** (wrangler OAuth cannot mint these):

1. Dashboard → R2 → Overview → **Manage** API Tokens → Create User API token  
   Permission: **Object Read & Write**, bucket `nexus-memory` only.
2. Copy Access Key ID + Secret Access Key once.

```bash
# From nexus-hashistack — only writes when R2 env vars are set
export NEXUS_GW_R2_ACCOUNT_ID=901cf745bc4091a67a1070c2d0d61574
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
# Sync secrets from Vault prod path (not nexus/dev lab MinIO keys)
NEXUS_VAULT_GW_PATH=nexus/prod ./deploy/scripts/sync-vault-to-k8s.sh

kubectl apply -k deploy/kubernetes/soc/overlays/r2
kubectl -n soc rollout restart deployment/nexus-api-gateway

# Re-apply bucket CORS after editing r2-cors.json:
# npx wrangler r2 bucket cors set nexus-memory --file deploy/kubernetes/soc/overlays/r2/r2-cors.json -y
```

Gateway env after patch: `NEXUS_GW_OBJECT_STORE_BACKEND=r2`, TLS on,
region `auto`, credentials from `nexus-gateway-secrets` (same key names as MinIO).

See `platform/api-gateway/OBJECT_STORE.md`.

## Full spine

This overlay uses the thin `console/` slice (no in-cluster MinIO). To attach the
same R2 patches to `base` (AI/MCP/Athena), copy the ConfigMap + gateway patch
and delete MinIO StatefulSet/Service as in `overlays/prod`.
