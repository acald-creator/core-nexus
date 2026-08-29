# Purple (Jupyter) + red (Athena standard) range package

GitOps target: `../overlays/gitops-range`. Keeps offensive/purple workloads off
the Console+gateway R2 spine (`../console`, `../overlays/r2`).

| Workload | Role | Image |
|----------|------|--------|
| `nexus-workbench` | JupyterLab purple workspace | `phoenixvlabs/nexus-workbench` |
| `nexus-athena` | Isolated standard Athena shell | `phoenixvlabs/nexus-athena` |

Elevated / packet-lab / agent profiles stay in `nexus-athena` overlays — not here.

## Lab RAM

Requests are minimal; Jupyter limit is 512Mi. Prefer ≥8Gi node memory before
adding Wazuh or elevated Athena alongside Argo/Flux.

```bash
kubectl apply -k deploy/kubernetes/soc/overlays/gitops-range
kubectl -n soc port-forward svc/nexus-workbench 8888:8888
# open http://localhost:8888  (lab image has empty notebook token)
kubectl -n soc exec -it deploy/nexus-athena -- bash
```
