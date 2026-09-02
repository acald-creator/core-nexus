# Overlay: hybrid sensor (compose-your-own SOC)

**ADR 0011** — Vector + Suricata + Zeek + Falco + Tetragon → ai-inference triage. **No Wazuh.**

Use this when you want the cybersecurity sensor stack without the Wazuh indexer/manager RAM cost.
For Wazuh + full test spine, use `overlays/test` instead. For thin Console + gateway only, use
`overlays/r2`.

## Prerequisites

- Kubernetes cluster (Rancher Desktop recommended, **≥8 Gi RAM** with all sensors)
- [nexus-hashistack](https://github.com/acald-creator/nexus-hashistack) Vault for gateway secrets
- `kubectl` with kustomize **helm support** (`--enable-helm`) for Vector, Tetragon, Falco charts

```bash
cd ../nexus-hashistack && ./scripts/nexus-dev-up.sh
cd ../core-nexus
./deploy/scripts/sync-vault-to-k8s.sh
```

## Apply

```bash
kubectl kustomize deploy/kubernetes/soc/overlays/hybrid-sensor --enable-helm | kubectl apply -f -
kubectl -n soc rollout status deployment/nexus-api-gateway
kubectl -n soc rollout status deployment/ai-inference
kubectl -n kube-system rollout status daemonset/suricata
```

## Verify

```bash
# Vector → ai-inference (watch triage record count grow after sensor traffic)
kubectl -n soc port-forward svc/ai-inference 8000:8000
curl -s http://127.0.0.1:8000/health

# Falco test (optional)
kubectl -n kube-system exec -it ds/falco -- falco --version
```

## Architecture

```
Suricata ──┐
Zeek     ──┼── Vector (kube-system) ──HTTP──► ai-inference (soc) ──► gateway triage API
Falco    ──┤
Tetragon ──┘
```

## Port-forward (Console)

```bash
kubectl -n soc port-forward svc/nexus-console 3000:80
kubectl -n soc port-forward svc/nexus-api-gateway 3100:3100
```

## Notes

- **Alert list in Console** still expects Wazuh when calling `GET /api/v1/alerts`; use triage
  deep-links or `POST /v1/triage` until gateway SOC-events adapter (ADR 0011 H2).
- **Zeek interface:** default `eth0`; patch `ZEEK_INTERFACE` in `system/zeek/daemonset.yaml` if
  capture fails on your node.
- **R2 object store:** this overlay uses lab gateway secrets (`nexus/dev`). For R2 blobs, apply
  `overlays/r2` patches separately or merge manually.

## Related

- `docs/decisions/0011-compose-soc-vector-zeek-falco-tetragon.md`
- `deploy/kubernetes/soc/overlays/hybrid-sensor/vector/vector-values-hybrid.yaml`
