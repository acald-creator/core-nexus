# Threat Model

Living document for Underground Nexus (`core-nexus`). Consumed by
`security-compliance-hub` DevSecOps plan phase.

## 1. System overview

**What does this system do?**
Programmable fabric + secure software factory with an attached red/blue/purple
range: Nexus Console and API gateway (blue/ops), Jupyter workbench (purple),
isolated Athena (red), optional Wazuh, object storage (MinIO lab / R2+D1 prod),
and GitOps (Argo + Flux) for signed image promotion.

**Users and actors**
Lab operators, SOC analysts (Console), purple analysts (Jupyter), red operators
(Athena/`athena-agents`), CI (SSF/cosign, security-compliance-hub), Flux image
automation, Argo CD.

**Trust boundaries**
- Public Hub registry → cluster (image pull; prefer signed OCI)
- Operator laptop → Vault / kubectl / Cloudflare (R2, D1 Worker)
- Gateway → Wazuh / Athena agents / object store / D1 metadata proxy
- Jupyter / Athena pods → lab network (keep red tooling out of workbench)
- GitHub Actions → Hub / Sigstore (when publish CI is enabled)

## 2. Assets

| Asset | Sensitivity | Where it lives |
|---|---|---|
| Gateway JWT + object-store keys | High | Vault `secret/nexus/prod`, K8s `nexus-gateway-secrets` |
| Wazuh API / indexer passwords | High | Vault `secret/soc/wazuh`, K8s `wazuh-secrets` |
| Cosign signing key | High | Operator `.tmp-review/cosign/` (gitignored); CI secrets when enabled |
| D1 metadata API key | High | Vault + Worker secret |
| Ground-truth / artifact blobs | Medium–High | R2 `nexus-memory` / MinIO |
| Architecture & threat docs | Low–Medium | This repo |

## 3. Threats (STRIDE)

| Category | Example | Mitigation |
|---|---|---|
| Spoofing | Forged registry tags | SSF/cosign sign + Flux pin digests/tags |
| Tampering | Unsigned image promote | Argo only syncs Git pins; prefer verify in policy |
| Repudiation | Unsigned CI publish | Sigstore tlog entries on `ssf sign` |
| Information disclosure | Secrets in Git | Vault + sync scripts; Gitleaks via security hub |
| Denial of service | Wazuh OOM on small nodes | Separate overlays; ≥8Gi for TLS Wazuh |
| Elevation of privilege | Athena capabilities | Profiles + capability drop; elevated overlays separate |

## 4. Out of scope (near term)

- Full OIDC for Console (local auth in lab)
- Production Vault HA / KMS auto-unseal
- GitHub publish CI secrets (on hold; local `ssf sign` used)

## 5. Related docs

- `docs/architecture/01-component-architecture.md` §0
- `deploy/gitops/README.md`, `platform/api-gateway/OBJECT_STORE.md`
- `platform/nexus-metadata/README.md`
