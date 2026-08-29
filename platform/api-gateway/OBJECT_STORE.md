# Object store (gateway)

Lab default is MinIO. Production can switch to Cloudflare R2 without changing
route code — both use the MinIO Python SDK (S3 API).

| Env | Lab | R2 prod |
|-----|-----|---------|
| `NEXUS_GW_OBJECT_STORE_BACKEND` | `minio` (default) | `r2` |
| `NEXUS_GW_MINIO_ENDPOINT` | `minio:9000` | omit (or set R2 API host) |
| `NEXUS_GW_R2_ACCOUNT_ID` | — | Cloudflare account id |
| `NEXUS_GW_MINIO_ACCESS_KEY` | MinIO key | R2 access key id |
| `NEXUS_GW_MINIO_SECRET_KEY` | MinIO secret | R2 secret access key |
| `NEXUS_GW_MINIO_BUCKET` | `nexus-memory` | R2 bucket name |
| `NEXUS_GW_MINIO_PUBLIC_ENDPOINT` | browser-reachable host | R2 public/custom domain host |
| `NEXUS_GW_OBJECT_STORE_REGION` | optional | `auto` (default for r2) |

D1 is reserved for **artifact/run metadata indexes** (not blobs). Wire a
separate index client when Flux/SSF digests need queryable provenance; keep
blobs on R2.
