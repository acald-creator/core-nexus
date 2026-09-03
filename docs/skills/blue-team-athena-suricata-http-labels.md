---
name: Athena Suricata HTTP Labels
description: Write Suricata rules for Athena-labeled HTTP stimulation (X-Athena-* headers, User-Agent, Juice Shop SQLi)
tags: [blue-team, suricata, athena, detection]
inclusion: manual
---

## When to Apply
- Adding custom Suricata rules for Athena OPAR or labeled-probe traffic
- Expanding `HTTP_PORTS` so lab targets (8090, 3001, 5173) are in scope
- Day 16-style “one rule for something Athena generated”

## Approach
1. Start from **observed** GT or probe traffic, not generic SQLi lists (those are Day 22).
2. Prefer the Athena **label headers** (`X-Athena-Scenario`, `X-Athena-Scenario-Id`, `X-Athena-Run-ID`) — they are the SOC contract, not a payload guess.
3. Keep custom SIDs in a reserved band (`20261601+` for 100 Days Day 16).
4. Mount rules via ConfigMap at `/etc/suricata/athena.rules`; include that path in `rule-files` **after** `suricata-update` emerging rules.
5. Expand `HTTP_PORTS` for lab services or the rule never fires on Night Quire / Juice Shop.
6. Host-native probes may **not** traverse the Suricata DaemonSet capture path (`platform/athena/README`). Rule existence ≠ eve.json hit.

## Key Patterns
- ConfigMap keys: `suricata.yaml`, `athena.rules`, `update-rules.sh`
- DaemonSet mounts `athena.rules` as a subPath
- Vector still tags `nexus.source=suricata` when eve.json has alerts

## Pitfalls
- Default `HTTP_PORTS: "80"` misses 8090/3001
- `suricata-update` overwrites `/var/lib/suricata/rules/suricata.rules` — do not put custom rules only there
- Broad `OR 1=1` URI matches will false-positive; tighten before production

## References
- `deploy/kubernetes/system/suricata/`
- `docs/decisions/0007-hybrid-sensor-suricata.md`
- `scripts/labeled-probe-session.py`
