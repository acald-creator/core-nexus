# Kubernetes Deployment

This directory holds Kubernetes manifests, Kustomize bases, Helm values, and related notes.

**Vault is not deployed here.** Use [nexus-hashistack](https://github.com/acald-creator/nexus-hashistack) for local Vault, or a shared cluster Vault later. See `deploy/kubernetes/soc/README.md`.

**Images:** SOC base Deployments use `phoenixvlabs/nexus-*` (same tags as
`./scripts/build-platform-images.sh` and `deploy/compose/dev.yml`). `imagePullPolicy:
IfNotPresent` so a local build/tag still works offline.

The near-term production-like path belongs here when it is not specifically UDS or Zarf packaging.
