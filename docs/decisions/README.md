# Architecture Decision Records

Short, durable decisions for Underground Nexus. Prefer these over chat history when
agents or humans need the locked defaults.

| ID | Title | Status |
| --- | --- | --- |
| [0001](0001-local-only-and-deprecated-components.md) | Local-only and deprecated components | Accepted |
| [0002](0002-product-spine-fabric-factory-range.md) | Product spine: fabric + factory + range | Accepted |
| [0003](0003-gitops-flux-and-argo.md) | GitOps: Flux image automation + Argo CD apps | Accepted |
| [0004](0004-secure-software-factory-ssf-kiln.md) | Factory: nebucloud/ssf + kiln | Accepted |
| [0005](0005-object-store-minio-lab-r2-d1-prod.md) | Objects: MinIO lab; R2 + D1 prod | Accepted |
| [0006](0006-human-clients-and-webtop-retirement.md) | Human clients; webtops retired | Accepted |
| [0007](0007-hybrid-sensor-suricata.md) | Hybrid sensor: Suricata + runtime telemetry | Accepted |
| [0008](0008-vault-ownership-nexus-hashistack.md) | Vault ownership: nexus-hashistack | Accepted |

## Format

```markdown
# Title
## Status
Accepted | Superseded by NNNN | Proposed
## Context
## Decision
## Consequences
```

## Agent memory

Load this directory (and `docs/architecture/01-component-architecture.md` §0) when
making architecture or deploy choices. Skill: `docs/skills/architecture-adr-decision-register.md`.

## When to add an ADR

- A non-negotiable changes or a new default is locked
- Lab-only vs production-like paths diverge
- Cross-repo ownership is clarified (Vault, Athena, factory)
