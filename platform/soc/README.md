# SOC Services

This directory is reserved for SOC service integration code as it migrates into `core-nexus`.

## Current Implementation

The SOC baseline stack (Wazuh + Suricata + analyst webtop) currently lives in the
`nexus-webtop-soc` repository:

| Asset | Location |
|-------|----------|
| Full compose stack | `nexus-webtop-soc/deploy/compose/soc-baseline.yml` |
| Suricata config | `nexus-webtop-soc/deploy/suricata/suricata.yaml` |
| Security bootstrap | `nexus-webtop-soc/scripts/bootstrap-wazuh-security.sh` |
| Operations guide | `nexus-webtop-soc/docs/soc-baseline.md` |

## Architecture References

- `docs/architecture/01-component-architecture.md` Section 3 — SOC Services target decomposition
- `docs/architecture/05-sensor-deep-dive.md` — Hybrid Suricata + runtime telemetry
- `docs/architecture/06-ai-soc-inference-engine.md` — AI triage integration

## Future

When SOC services move from `nexus-webtop-soc` compose definitions into Kubernetes manifests
or Helm charts, the implementation code will land here.
