# Local-Only and Deprecated Components

## Status

Accepted

## Context

Underground Nexus still carries a useful Docker-based lab profile, but several lab conveniences should not be confused with the production-like Kubernetes/UDS direction or the future Zevn/TerranoxOS target.

## Decision

The following components are local-only, experimental, or deprecated as production directions:

| Component | Status | Direction |
| --- | --- | --- |
| Portainer CE | Local-only | Keep for Docker lab visibility; replace with Argo CD for production-like GitOps. |
| Pi-hole | Local-only | Keep for lab DNS filtering; use Kubernetes DNS, network policy, and Istio for cluster and service traffic control. |
| Vault dev mode | Local-only | Keep for learning and local workflows; replace with Vault HA or an equivalent production secrets design. |
| Privileged Docker-in-Docker image | Local-only | Keep for the bootstrap lab; avoid as the production runtime model. |
| Sysbox image | Experimental | Keep as an alternate lab runtime until its role is revalidated. |
| Docker Swarm bootstrap | Deprecated direction | Keep only while needed by the legacy script; prefer Kubernetes for future orchestration. |
| Hard-coded lab IPs and default credentials | Deprecated direction | Replace with profile configuration, generated secrets, and documented access patterns. |

## Consequences

- Architecture documents should describe these components as lab-only when they appear.
- Production-like work should target Kubernetes, Argo CD, Vault HA, observability, and approved UDS/Zarf packaging where applicable.
- Future Zevn/TerranoxOS work should remain separate from the local Docker lab profile.
