# Local-Only and Deprecated Components

## Status

Accepted

## Context

Underground Nexus still carries a useful Docker-based lab profile, but several lab conveniences should not be confused with the production-like Kubernetes/UDS direction or the future Enterprise Platform/SecureOS target.

## Decision

The following components are local-only, experimental, or deprecated as production directions:

| Component | Status | Direction |
| --- | --- | --- |
| Portainer CE | Local-only | Keep for Docker lab visibility; replace with Argo CD for production-like GitOps. |
| Pi-hole | Local-only | Keep for lab DNS filtering; use Kubernetes DNS, network policy, and Istio for cluster and service traffic control. |
| Vault (HashiCorp) | External (nexus-hashistack) | Do not deploy Vault from core-nexus; consume AppRole / VAULT_ADDR from the sibling HashiStack (lab) or a shared cluster Vault (later). |
| Privileged Docker-in-Docker image | Local-only | Keep for the bootstrap lab; avoid as the production runtime model. |
| Sysbox image | Experimental | Keep as an alternate lab runtime until its role is revalidated. |
| Docker Swarm bootstrap | Deprecated direction | Keep only while needed by the legacy script; prefer Kubernetes for future orchestration. |
| Hard-coded lab IPs and default credentials | Deprecated direction | Replace with profile configuration, generated secrets, and documented access patterns. |

## Consequences

- Architecture documents should describe these components as lab-only when they appear.
- Production-like work should target Kubernetes, Argo CD, shared Vault (via nexus-hashistack / platform Vault), observability, and approved UDS/Zarf packaging where applicable.
- Future Enterprise Platform/SecureOS work should remain separate from the local Docker lab profile.
- core-nexus must not reintroduce in-cluster Vault Deployments; keep secrets ownership in HashiStack / shared Vault.
