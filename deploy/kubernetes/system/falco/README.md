# Falco (runtime detection)

Helm chart for [Falco](https://falco.org/) — syscall/K8s runtime rules.

Used by `deploy/kubernetes/soc/overlays/hybrid-sensor` (ADR 0011). Vector scrapes JSON logs
from pods labeled `app.kubernetes.io/name=falco`.

```bash
kubectl apply -k deploy/kubernetes/system/falco
```

Requires eBPF support (Rancher Desktop / Linux nodes). On macOS RD, ensure Kubernetes is
enabled and the node has sufficient RAM (≥8 Gi recommended with other sensors).
