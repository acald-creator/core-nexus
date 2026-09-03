# UDS and Zarf Deployment

Zarf packages for air-gapped or connected delivery of the **hybrid-sensor** lab stack
(ADR 0011). UDS is a delivery option — **not** the secrets backend. Vault stays in
[nexus-hashistack](https://github.com/acald-creator/nexus-hashistack).

Day-2 GitOps (Flux / Argo CD) remains the connected drift path. Zarf packages the same
Kubernetes workloads for first delivery or offline media.

## Packages

| Package | Path | Contents |
| --- | --- | --- |
| `nexus-platform` | [`nexus-platform/`](nexus-platform/) | Console, API gateway, ai-inference (`phoenixvlabs/*:v0.2.6`) |
| `nexus-hybrid-sensor` | [`nexus-hybrid-sensor/`](nexus-hybrid-sensor/) | Suricata, Zeek, Falco, Tetragon, Vector → triage; sets `NEXUS_GW_ALERTS_SOURCE=triage` |
| `nexus-airgap-ops` | [`nexus-airgap-ops/`](nexus-airgap-ops/) | Files-only: `nexus-tui` + Day 19 terminal runbooks (no images) |

Deploy order: **platform → hybrid-sensor** (cluster). **airgap-ops** is optional operator media.

## Wrapper

```bash
./deploy/uds/create-packages.sh                 # TUI binary + airgap-ops tarball
ZARF_CREATE_IMAGES=1 ./deploy/uds/create-packages.sh   # also pull platform/sensor images
```

## Prerequisites

### 1. Local Zarf CLI (built from source)

This repo expects a locally built CLI (not necessarily a release binary from elsewhere).

```bash
# Clone once (or use your existing clone)
git clone https://github.com/zarf-dev/zarf.git ~/zarf
cd ~/zarf
git fetch --tags
git checkout v0.84.0   # or newer stable tag
make build

mkdir -p ~/bin
ln -sfn ~/zarf/build/zarf-mac-apple ~/bin/zarf   # Darwin arm64; use build/zarf on Linux amd64
export PATH="$HOME/bin:$PATH"
zarf version   # expect v0.84.0 (or the tag you checked out)
```

Built and verified for this milestone: **zarf v0.84.0** (`~/zarf` @ tag `v0.84.0`).

### 2. Vault secrets for the gateway

```bash
cd ../nexus-hashistack && ./scripts/nexus-dev-up.sh
cd ../core-nexus
./deploy/scripts/sync-vault-to-k8s.sh
```

### 3. Cluster

Kubernetes context ready (e.g. Rancher Desktop). For a clean Zarf deploy, prefer an empty
`soc` / sensor set — do not interleave with an already-applied `kubectl` hybrid-sensor
overlay unless you intend to upgrade in place.

## Create packages (connected builder)

From the `core-nexus` repo root (images are pulled into the tarball):

```bash
export PATH="$HOME/bin:$PATH"

zarf package create deploy/uds/nexus-platform \
  -o dist/uds --confirm

zarf package create deploy/uds/nexus-hybrid-sensor \
  -o dist/uds --confirm
```

Inspect:

```bash
zarf package inspect definition dist/uds/zarf-package-nexus-platform-*.tar.zst
zarf package inspect images dist/uds/zarf-package-nexus-platform-*.tar.zst
zarf package inspect definition dist/uds/zarf-package-nexus-hybrid-sensor-*.tar.zst
zarf package inspect images dist/uds/zarf-package-nexus-hybrid-sensor-*.tar.zst
```

(`dist/uds/` is gitignored build output.)

## Deploy (lab or air-gap)

```bash
export PATH="$HOME/bin:$PATH"

# Optional if Zarf is not initialized on the cluster yet:
# zarf init --confirm

zarf package deploy dist/uds/zarf-package-nexus-platform-*.tar.zst --confirm
zarf package deploy dist/uds/zarf-package-nexus-hybrid-sensor-*.tar.zst --confirm
```

### Verify

```bash
kubectl -n soc get deploy,pods
kubectl -n soc get deploy nexus-api-gateway \
  -o jsonpath='{.spec.template.spec.containers[0].env}' | tr ',' '\n' | grep ALERTS
kubectl -n kube-system get ds falco tetragon vector
kubectl -n soc get ds suricata zeek

kubectl -n soc port-forward svc/nexus-console 3000:80
kubectl -n soc port-forward svc/nexus-api-gateway 3100:3100
```

Full `zarf package deploy` into a cluster that already runs the kubectl hybrid-sensor overlay
is **optional follow-on** for this milestone — prefer create + inspect first.

## Connected path (unchanged)

Without Zarf, apply the overlay as usual:

```bash
kubectl kustomize deploy/kubernetes/soc/overlays/hybrid-sensor --enable-helm | kubectl apply -f -
```

See [`../kubernetes/soc/overlays/hybrid-sensor/README.md`](../kubernetes/soc/overlays/hybrid-sensor/README.md).

## Non-goals (this milestone)

- UDS Core (SSO, Istio, Velero, …)
- CI workflow publishing `.tar.zst` artifacts
- Wazuh / `overlays/test` Zarf package
- Athena / Workbench container packages (operator TUI is `nexus-airgap-ops`)

## Related

- ADR 0011 — compose-your-own SOC
- `docs/architecture/02-enterprise-production-setup.md` §7 (UDS / Zarf relationship)
- Legacy webtop packaging (retired): `nexus-webtop-soc/deploy/zarf` — not a current product surface
