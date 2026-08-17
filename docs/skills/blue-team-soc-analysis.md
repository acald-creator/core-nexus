---
name: SOC Blue Team Analysis
description: Structured approach for SOC analyst workflows, detection engineering, and incident response
tags: [blue-team, soc, detection, incident-response]
inclusion: manual
---

## When to Apply
- Working in nexus-webtop-soc or SOC-related compose stacks
- Analyzing Wazuh alerts, Suricata rules, or sensor telemetry
- Building detection rules or tuning alert thresholds
- Investigating incidents using the analyst webtop
- Configuring the SOC baseline stack

## Approach
1. Start with the compose stack topology: `deploy/compose/soc-baseline.yml`
2. Identify which service generated the alert (Wazuh manager, Suricata sensor, or custom)
3. Check Suricata rule files for existing coverage of the indicator
4. Cross-reference with Wazuh decoder/rule XML for correlation
5. Use the analyst webtop for visual investigation (XFCE + browser + CLI tools)
6. Document findings as structured JSON ground-truth records
7. If new detection is needed, write rule + test case together
8. Validate with `scripts/validate-analyst-image.sh` after changes

## Key Patterns
- Compose services use dotted names: `wazuh.manager`, `suricata.sensor`, `webtop.analyst`
- Bootstrap security after `down -v`: `scripts/bootstrap-wazuh-security.sh`
- Suricata config: `deploy/suricata/suricata.yaml`
- Image override: `WEBTOP_ANALYST_IMAGE` env var
- Detection services are dedicated containers, NOT inside the desktop image
- Analyst image acceptance gate: healthchecks, curl, tool availability

## Pitfalls
- Don't add SOC control-plane services into the desktop image
- Don't modify cert paths in bootstrap script without updating indexer layout
- Don't hardcode credentials in Dockerfiles or scripts
- The webtop is for analyst workflow, not for running detection engines
- Always run acceptance gate before considering changes complete

## References
- `nexus-webtop-soc/deploy/compose/soc-baseline.yml` — full stack
- `nexus-webtop-soc/deploy/suricata/suricata.yaml` — sensor config
- `nexus-webtop-soc/scripts/bootstrap-wazuh-security.sh` — security init
- `nexus-webtop-soc/scripts/validate-analyst-image.sh` — acceptance gate
- `nexus-webtop-soc/docs/soc-baseline.md` — operations guide
