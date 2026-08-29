# Sensors

This directory is reserved for hybrid sensor integration code (Suricata + runtime/kernel telemetry).

## Current Implementation

Suricata is deployed from this monorepo’s Kubernetes tree (not from webtop images):

| Asset | Location |
|-------|----------|
| Suricata DaemonSet | `deploy/kubernetes/system/suricata/` |
| Wired from | `deploy/kubernetes/soc/overlays/test` |
| Runtime telemetry | Tetragon (`deploy/kubernetes/system/tetragon`) — see `docs/scenarios/` |

Archived compose recipes may exist under `nexus-webtop-soc`; do not use them as the
recommended path.

## Architecture References

- `docs/architecture/05-sensor-deep-dive.md` — Full sensor architecture (Suricata + runtime)
- `docs/architecture/01-component-architecture.md` Section 5 — Network and traffic capture decisions

## Future

When hybrid sensor config or operators land beside the DaemonSet, keep them under
`deploy/kubernetes/system/suricata` / this directory — not in webtop images.
Tetragon provides runtime/kernel telemetry alongside Suricata.
