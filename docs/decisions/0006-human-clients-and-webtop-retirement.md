# Human Clients and Webtop Retirement

## Status

Accepted

## Context

Full Linux SOC/analyst desktops (`nexus-webtop-soc`, `nexus-webtop-workbench`)
bundled control-plane and tooling into images that are hard to harden, GitOps, and
reason about. They conflicted with a fabric model where Console, Jupyter, and
Athena are separate surfaces.

## Decision

**Keep as human client surfaces:**

| Surface | Role |
| --- | --- |
| Nexus Console | Blue ops UX (launchpad, alerts, approvals, artifacts) |
| Jupyter purple workspace | `platform/workbench` / `nexus-workbench` |
| Isolated Athena | Red range container (+ `athena-agents`) |
| Optional `nexus-tui` | Constrained / air-gapped terminal client |

**Retire as product images:** `nexus-webtop-soc` and `nexus-webtop-workbench`.

- Do not put SOC control-plane or factory trust into desktop images.
- Transitional compose may remain in those repos as **archive** until headless SOC
  in `core-nexus` is sufficient; do not re-add webtop Git remotes to k8s `base/`.
- Prefer `deploy/kubernetes/soc/` for SOC platform docs and manifests.

## Consequences

- README and AGENTS mark webtops archive-only.
- Console launchpad deep-links target Console routes, Jupyter, gateway docs, Vault —
  not Portainer/Pi-hole as primary product tiles.
