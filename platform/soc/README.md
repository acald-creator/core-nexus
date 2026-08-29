# SOC Services

SOC integration and migration notes for Underground Nexus.

## Product rule

SOC is **headless services** (Wazuh, sensors, AI triage) plus **Nexus Console** /
`nexus-tui` for humans. Do **not** put detection engines or control-plane into
desktop/webtop images (`docs/architecture/01-component-architecture.md` §0).

## Current Implementation

| Asset | Location |
|-------|----------|
| Kubernetes SOC (preferred in-repo path) | `deploy/kubernetes/soc/` |
| Vault → k8s secret sync | `deploy/scripts/sync-vault-to-k8s.sh` |
| Transitional compose (legacy repo) | `nexus-webtop-soc` — recipes only; webtop client retired |

## Architecture References

- `docs/architecture/01-component-architecture.md` — narrative + SOC decomposition
- `docs/architecture/05-sensor-deep-dive.md` — Hybrid Suricata + runtime telemetry
- `docs/architecture/06-ai-soc-inference-engine.md` — AI triage integration
