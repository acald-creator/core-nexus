# Sensors

This directory is reserved for hybrid sensor integration code (Suricata + runtime/kernel telemetry).

## Current Implementation

Suricata runs as a dedicated container in the SOC baseline compose stack:

| Asset | Location |
|-------|----------|
| Suricata container | `nexus-webtop-soc/deploy/compose/soc-baseline.yml` (service: `suricata.sensor`) |
| Suricata config | `nexus-webtop-soc/deploy/suricata/suricata.yaml` |
| Runtime telemetry | Tetragon (in UDS Core baseline) — see scenarios in `docs/scenarios/` |

## Architecture References

- `docs/architecture/05-sensor-deep-dive.md` — Full sensor architecture (Suricata + runtime)
- `docs/architecture/01-component-architecture.md` Section 5 — Network and traffic capture decisions

## Future

When the hybrid sensor moves from compose into Kubernetes (DaemonSet, sidecar, or gateway),
the manifests and integration code will land here. Tetragon integration from UDS Core
provides the runtime/kernel telemetry side.
