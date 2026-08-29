# Console + API gateway package

Minimal blue/ops slice for GitOps (`overlays/r2` via Argo `nexus-gitops-lab`).
Manifests are a focused copy of the matching files under `../base` so kustomize
load restrictions stay happy without pulling Athena/MinIO or retired webtop remotes.

When editing gateway/console Deployments, update **both** `base/` and
`console/` until these are unified (single source + deletions).
