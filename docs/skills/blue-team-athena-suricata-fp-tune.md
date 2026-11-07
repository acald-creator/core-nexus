---
name: Athena Suricata Labeled-Traffic FP Tuning
description: Reduce Suricata false positives from Athena labeled and dir-bruteforce traffic (thresholds, UA gates, scenario header)
tags: [blue-team, suricata, athena, false-positives, tuning]
inclusion: manual
---

## When to Apply
- Day 25-style Use after labeled probe storms drown the SOC
- SID 20262401 (or similar UA rules) fires once per GET
- Policy SIDs 20261601/20261602 alert on every Athena request
- Path rules (`/.git`, `/wp-admin`) must not claim “Athena dirbrute” without the tool UA

## Approach
1. **Beacon labels** — `threshold: type limit, track by_src, count 1, seconds 120` on 20261601/20261602 (presence, not per-request).
2. **Dirbrute storm** — `threshold: type both, track by_src, count 8, seconds 30` on 20262401 (alert after volume, once per window).
3. **Path SIDs** — require `http.user_agent; content:"athena-agents/dir-bruteforce"` on 20262402/203.
4. **SQLi SIDs** — gate 20261603 and 20262201–203 on `X-Athena-Scenario` so random URI/body noise is not attributed to Athena.
5. Bump `rev:` on every tuned rule; apply ConfigMap, restart DaemonSet, wait ~25s, re-probe.

## Key Patterns
- ConfigMap: `deploy/kubernetes/system/suricata/suricata-config.yaml` → `athena.rules`
- Verify: `scripts/day25-suricata-fp-tune.sh` (ns `soc`; reuse `day24-dirbrute-probe.sh`)
- Day 24 baseline (one ~23-GET run): 20262401×46; after Day 25 tune: 20262401×2 (dual-iface dup)

## Pitfalls
- Applying ConfigMap without `-n soc` (or `kubectl apply -k ... -n soc`) creates a orphan CM in `default`
- `type limit` vs `type both` — limit = first hit then silence; both = wait for count then silence
- Juice Shop SPA **200** for missing paths remains; path alerts mean *probe*, not *exposure*
- Dual iface (eth0 + vznat) can still double counts — tune for volume order-of-magnitude, not exact 1

## References
- `docs/skills/blue-team-athena-dirbrute-suricata.md`
- `docs/skills/blue-team-suricata-multi-iface-capture.md`
- Day 24 / Day 25 challenge tracker entries
