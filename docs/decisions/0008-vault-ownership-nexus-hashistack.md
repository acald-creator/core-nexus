# Vault Ownership: nexus-hashistack

## Status

Accepted

## Context

Vault Deployments inside `core-nexus` duplicated ownership with
`nexus-hashistack`, drifted from AppRole export workflows, and encouraged
treating core-nexus GitOps as the secrets control plane.

## Decision

- **Vault is not deployed from `core-nexus`** (no Helm chart / StatefulSet under
  this repo’s default manifests).
- Lab and local Vault (+ optional Consul) are owned by
  [`nexus-hashistack`](https://github.com/acald-creator/nexus-hashistack).
- Later shared/platform Vault may replace the sidecar; ownership stays outside
  core-nexus application GitOps.
- Workloads consume Vault via `VAULT_ADDR`, AppRole, and
  `deploy/scripts/sync-vault-to-k8s.sh` (e.g. `NEXUS_VAULT_GW_PATH=nexus/prod` for R2).
- Console login remains **gateway JWT** (`authProvider: local`); Vault UI is a
  deep-link, not the Console IdP.

Topology sketches in `docs/architecture/12-vault-environments-specification.md`
describe Vault *as operated by hashistack / platform Vault ops*, not as Argo-synced
resources from this repository.

## Consequences

- Docs must not recommend “install Vault via Argo/Helm from core-nexus.”
- ADR 0001 Vault row and this ADR are the durable ownership record.
- Production HA/auto-unseal is a hashistack / platform concern; Phase 1 exit is
  “consume hashistack patterns,” not “stand up Vault StatefulSet here.”
