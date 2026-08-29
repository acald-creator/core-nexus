#!/usr/bin/env bash
# Sketch bootstrap: Argo CD (apps) + Flux (image automation only).
# Not production-hardened. See deploy/gitops/README.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GITOPS="${ROOT}/deploy/gitops"

NEXUS_GIT_URL="${NEXUS_GIT_URL:-https://github.com/acald-creator/core-nexus.git}"
NEXUS_GIT_BRANCH="${NEXUS_GIT_BRANCH:-main}"
ARGO_VERSION="${ARGO_VERSION:-stable}"

echo "==> Namespaces"
kubectl get ns argocd >/dev/null 2>&1 || kubectl create namespace argocd
kubectl get ns flux-system >/dev/null 2>&1 || kubectl create namespace flux-system

echo "==> Argo CD (${ARGO_VERSION})"
# Server-side apply avoids CRD annotation size limit on kubectl client-side apply.
kubectl apply --server-side --force-conflicts -n argocd \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGO_VERSION}/manifests/install.yaml"
echo "    waiting for argocd-server..."
kubectl -n argocd rollout status deployment/argocd-server --timeout=240s || true

echo "==> Flux controllers (source + image-reflector + image-automation)"
if command -v flux >/dev/null 2>&1; then
  flux install \
    --namespace=flux-system \
    --components=source-controller,image-reflector-controller,image-automation-controller \
    --network-policy=false
else
  echo "WARNING: flux CLI not found; installing via fluxcd install.yaml (full default components)."
  echo "         Prefer: brew install fluxcd/tap/flux  then re-run for a lean install."
  kubectl apply -f https://github.com/fluxcd/flux2/releases/latest/download/install.yaml
fi

echo "==> Patch Argo root Application repo/branch placeholders"
TMP_ROOT="$(mktemp)"
sed \
  -e "s|__NEXUS_GIT_URL__|${NEXUS_GIT_URL}|g" \
  -e "s|__NEXUS_GIT_BRANCH__|${NEXUS_GIT_BRANCH}|g" \
  "${GITOPS}/argo/root-application.yaml" >"${TMP_ROOT}"
kubectl apply -f "${TMP_ROOT}"
rm -f "${TMP_ROOT}"

echo "==> Flux image automation manifests"
kubectl apply -k "${GITOPS}/flux"

echo
echo "SUCCESS (sketch). Next:"
echo "  1. Create flux-system git credentials from flux/git-secret.example.yaml"
echo "  2. kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
echo "  3. kubectl -n argocd port-forward svc/argocd-server 8080:443"
echo "  4. Confirm Application nexus-gitops-lab syncs"
echo "  5. Read deploy/gitops/ssf-follow-on.md for OCI → Flux path"
echo
echo "Git remote used: ${NEXUS_GIT_URL} @ ${NEXUS_GIT_BRANCH}"
