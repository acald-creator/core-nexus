# Object Store: MinIO Lab; Cloudflare R2 + D1 Prod

## Status

Accepted

## Context

MinIO is the right S3-shaped lab dependency, but production-like Nexus should not
assume an in-cluster MinIO HA StatefulSet as the default blob store. Artifact
*metadata* (runs, indexes) also needs a durable query path separate from blobs.

## Decision

| Environment | Blobs | Metadata |
| --- | --- | --- |
| Lab | MinIO (S3 API) | Local/lab indexes as configured |
| Production-like | Cloudflare **R2** (`NEXUS_GW_OBJECT_STORE_BACKEND=r2`) | Cloudflare **D1** via `platform/nexus-metadata` Worker |

- Gateway object client: `platform/api-gateway` (`OBJECT_STORE.md`).
- R2 overlay: `deploy/kubernetes/soc/overlays/r2` (Argo `nexus-gitops-lab`).
- Artifact/run API: gateway `/api/v1/artifact-index`, `/api/v1/runs`.
- MinIO remains valid for compose and MinIO-era overlays (`gitops-lab`, `dev`).

MinIO is **not** the SOC event database (Wazuh indexer) or platform log store (Loki).

## Consequences

- Architecture §6 no longer presents MinIO Helm HA as the default prod object store.
- Console/gateway docs mention MinIO lab / R2+D1 prod.
- Skills and PCAPs may live in the active object backend for the environment.
