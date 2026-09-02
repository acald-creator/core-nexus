# Falco (runtime detection)

Helm chart for [Falco](https://falco.org/) — syscall/K8s runtime rules.

Used by `deploy/kubernetes/soc/overlays/hybrid-sensor` (ADR 0011). Vector scrapes JSON logs
from pods labeled `app.kubernetes.io/name=falco`.

```bash
kubectl apply -k deploy/kubernetes/system/falco
```

Requires eBPF support (Rancher Desktop / Linux nodes). Chart defaults to `modern_ebpf`
for lab nodes without kernel headers. On macOS RD, if Falco init still fails, rely on
**Tetragon** for runtime telemetry (ADR 0011) and disable Falco in the overlay.
