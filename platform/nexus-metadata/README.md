# Nexus metadata index (Cloudflare D1)

Queryable **artifact/run provenance** for Flux/SSF digests. Blobs stay on R2
(`nexus-memory`); this Worker + D1 hold the index.

| Resource | Value |
|----------|--------|
| D1 database | `nexus-metadata` |
| Database ID | `465c1e0f-bf27-4154-8342-038369de45d8` |
| Worker | `nexus-metadata` (workers.dev) |

## Deploy

```bash
export PATH="/opt/homebrew/opt/node@26/bin:$PATH"
cd platform/nexus-metadata
npx wrangler@latest d1 execute nexus-metadata --remote --file=./schema.sql
npx wrangler@latest deploy
# non-interactive secret:
printf '%s' "$NEXUS_GW_D1_API_KEY" | npx wrangler@latest secret put API_KEY
```

Gateway env (R2 overlay / Vault `secret/nexus/prod`):

| Env | Purpose |
|-----|---------|
| `NEXUS_GW_D1_PROXY_URL` | `https://nexus-metadata.<subdomain>.workers.dev` |
| `NEXUS_GW_D1_API_KEY` | Same value as Worker `API_KEY` secret |

Lab MinIO overlays leave these unset — metadata client is a no-op.
