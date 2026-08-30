# GitOps bootstrap sketch (Flux + Argo CD)

**Status:** sketch / lab bootstrap — not a production install guide.  
**Narrative:** `docs/architecture/01-component-architecture.md` §0, `02` §5.

## Split of responsibility

| Tool | Owns | Does not own |
|------|------|----------------|
| **Argo CD** | Application delivery & UI: sync kustomize paths from this repo into the cluster | Image tag discovery |
| **Flux** | Image automation: watch registry → commit digest/tag updates to Git | Competing full-cluster Kustomizations (avoid dual reconcilers) |
| **SSF + kiln** | Sign / attest / SBOM / policy on build outputs (`nebucloud/ssf`) | Cluster sync |

```
build → kiln → ssf (sign/policy) → registry
                                      ↓
                              Flux ImageRepository
                                      ↓
                         commit image pin to Git
                                      ↓
                              Argo CD sync
                                      ↓
                                 cluster
```

Do **not** enable Flux `Kustomization` resources that sync the same paths Argo deploys. This sketch uses Flux **image-reflector + image-automation only**.

## Layout

```
deploy/gitops/
  README.md                 ← this file
  bootstrap.sh              ← install Argo + Flux controllers; apply sketch
  argo/
    root-application.yaml   ← app-of-apps
    applications/
      nexus-gitops-lab.yaml   ← Console + gateway (path → overlays/r2)
      nexus-gitops-range.yaml ← Jupyter + Athena standard
  flux/
    namespace.yaml
    kustomization.yaml
    git-secret.example.yaml ← copy → flux-system; do not commit credentials
    image-repositories.yaml
    image-policies.yaml
    image-update-automation.yaml
  ssf-follow-on.md          ← next work in nebucloud/ssf (OCI → this loop)
```

First Argo target overlay for Console + gateway: `deploy/kubernetes/soc/overlays/r2`
(R2 object store). Range workloads: `overlays/gitops-range`. MinIO-era local pins:
`overlays/gitops-lab` (not the live Argo lab destination — ADR 0003).

## Prerequisites

- Kubernetes cluster (Rancher Desktop / k3d / etc.) with enough RAM for Argo + Flux (~2+ Gi free beyond workloads)
- `kubectl`, `flux` CLI (optional but recommended), network to pull install manifests
- Git push credentials for Flux image automation (see `flux/git-secret.example.yaml`)
- Container registry reachable for `phoenixvlabs/nexus-*` (or fork ImageRepository URLs)

## Bootstrap

```bash
# From core-nexus root
export NEXUS_GIT_URL="https://github.com/acald-creator/core-nexus.git"  # your fork/remote
export NEXUS_GIT_BRANCH="main"
./deploy/gitops/bootstrap.sh
```

Then create the Flux git credentials secret (never commit it) and patch ImageUpdateAutomation if your remote/branch differ.

## Verify

```bash
kubectl -n argocd get applications
kubectl -n flux-system get imagerepository,imagepolicy,imageupdateautomation
argocd app get nexus-gitops-lab   # if argocd CLI configured
```

## After this sketch

1. Wire real git credentials + registry auth for private images.
2. Expand Argo apps (Wazuh HTTP lab, then secure overlay when node RAM allows).
3. Implement OCI in `nebucloud/ssf` and publish signed digests Flux can pin — see `ssf-follow-on.md`.
