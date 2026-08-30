# GitOps: Flux Image Automation + Argo CD App Delivery

## Status

Accepted

## Context

Portainer and manual `kubectl` are useful for labs but are not the production-like
delivery loop. Using both Flux and Argo as full-cluster reconcilers on the same
paths causes dual ownership and drift fights.

## Decision

Default programmatic fabric loop:

| Tool | Owns | Does not own |
| --- | --- | --- |
| **Flux** | Image reflector + image automation (registry → Git pin commits) | Competing Flux `Kustomization` sync of the same paths Argo deploys |
| **Argo CD** | Application delivery, UI, RBAC, sync of kustomize overlays | Image tag discovery |

Bootstrap sketch: `deploy/gitops/`.

**Current Argo lab apps:**

| Application | Path |
| --- | --- |
| `nexus-gitops-lab` | `deploy/kubernetes/soc/overlays/r2` (Console + gateway on R2) |
| `nexus-gitops-range` | `deploy/kubernetes/soc/overlays/gitops-range` (Jupyter + Athena) |

`overlays/gitops-lab` remains the MinIO-era / local pin overlay; it is **not** the
live Argo lab destination.

Portainer CE stays **lab-only** host visibility (see ADR 0001).

## Consequences

- Architecture docs say **Flux + Argo**, not Argo alone.
- Image tags advance via Flux commits; Argo syncs Git.
- Do not add Flux Kustomizations that apply the same SOC overlays Argo owns.
