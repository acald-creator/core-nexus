# Local-Only and Deprecated Components

## Status

Accepted

## Context

Underground Nexus still carries a useful Docker-based lab profile, but several lab conveniences should not be confused with the production-like Kubernetes/GitOps direction or the future Enterprise Platform/SecureOS target.

## Decision

The following components are local-only, experimental, or deprecated as production directions:

| Component | Status | Direction |
| --- | --- | --- |
| Portainer CE | Local-only | Keep for Docker lab visibility; production-like GitOps is **Flux + Argo CD** (ADR 0003). |
| Pi-hole | Local-only | Keep for lab DNS filtering; use Kubernetes DNS, network policy, and mesh controls for cluster traffic. |
| Vault (HashiCorp) | External | **Do not deploy from core-nexus** — ADR 0008 / `nexus-hashistack`. |
| Privileged Docker-in-Docker image | Local-only | Keep for the bootstrap lab; avoid as the production runtime model. |
| Sysbox image | Experimental | Keep as an alternate lab runtime until its role is revalidated. |
| Docker Swarm bootstrap | Deprecated direction | Prefer Kubernetes for orchestration. |
| Hard-coded lab IPs and default credentials | Deprecated direction | Replace with profile configuration and Vault-backed secrets. |
| `nexus-webtop-soc` / `nexus-webtop-workbench` | Retired product | Archive only — ADR 0006. |

## Consequences

- Architecture documents describe these components as lab-only or retired when they appear.
- Production-like work targets Kubernetes, **Flux + Argo CD**, shared Vault via hashistack, observability, and optional UDS/Zarf.
- Future Enterprise Platform/SecureOS work stays separate from the local Docker lab profile.
- core-nexus must not reintroduce in-cluster Vault Deployments.
