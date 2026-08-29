---
name: SOC Blue Team Analysis
description: Structured approach for SOC analyst workflows, detection engineering, and incident response
tags: [blue-team, soc, detection, incident-response]
inclusion: manual
---

## When to Apply
- Working on headless SOC (Wazuh, Suricata) in `core-nexus` k8s or transitional compose
- Analyzing Wazuh alerts, Suricata rules, or sensor telemetry
- Building detection rules or tuning alert thresholds
- Investigating via Nexus Console, Jupyter purple workspace, or `nexus-tui` (not webtop desktops)

## Approach
1. Prefer `deploy/kubernetes/soc/` in core-nexus; treat `nexus-webtop-soc` as **retired** (archive only)
2. Identify which service generated the alert (Wazuh manager, Suricata sensor, or custom)
3. Check Suricata rule files for existing coverage of the indicator
4. Cross-reference with Wazuh decoder/rule XML for correlation
5. Investigate in Console / Jupyter / TUI — not XFCE webtops
6. Document findings as structured JSON ground-truth records
7. If new detection is needed, write rule + test case together
8. Validate manifests/scripts appropriate to the path you changed (kustomize / compose)

## Key Patterns
- Detection services are dedicated containers, NOT inside desktop images
- Webtop analyst images are retired as product surfaces (`docs/architecture/01` §0)
- Secrets: Vault via hashistack + `sync-vault-to-k8s.sh`

## Pitfalls
- Don't add SOC control-plane services into desktop images
- Don't hardcode credentials in Dockerfiles or scripts
- Don't revive webtops as the recommended analyst path

## References
- `docs/architecture/01-component-architecture.md` §0
- `deploy/kubernetes/soc/` — in-repo SOC path
- `platform/soc/README.md`
- Retired: `nexus-webtop-soc` compose recipes (do not revive as the default stack)
