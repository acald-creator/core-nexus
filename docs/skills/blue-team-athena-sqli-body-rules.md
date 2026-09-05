---
name: Athena Suricata SQLi Body Rules
description: Write Suricata rules for Athena Juice Shop SQLi beyond URI OR 1=1 — request body tautology and raw URI %27
tags: [blue-team, suricata, athena, sqli, detection]
inclusion: manual
---

## When to Apply
- Closing the Day 21 gap: login POST JSON SQLi never hit URI-only SID 20261603
- Adding Athena SQLi SIDs in the `2026220x` band
- Debugging why `%27` rules never fire

## Approach
1. Observe wire payloads first (`eve.json` `payload_printable` / `http_request_body`).
2. Body tautology: `http.request_body; content:"OR 1=1";` (SID 20262201).
3. Body quote-OR comment: `http.request_body; content:"' OR"; content:"--"; within:40;` (SID 20262202).
4. Search quote injection: use **`http.uri.raw`** with `content:"%27"` — `http.uri` normalizes `%27` → `'` so a `%27` match never fires (SID 20262203).
5. After DaemonSet restart, wait ~25s before probing (engine start ≠ inspect-ready).

## Key Patterns
- ConfigMap: `deploy/kubernetes/system/suricata/suricata-config.yaml` → `athena.rules`
- Verify: `scripts/day22-athena-sqli-rules.sh`
- Probe path: in-cluster → `host.docker.internal:3003` (Day 21 multi-iface)

## Pitfalls
- Matching `%27` on normalized `http.uri`
- Probing within a few seconds of Suricata restart → zero alerts
- Expecting body rules to fire on GET query strings (those stay in URI)

## References
- `docs/skills/blue-team-athena-suricata-http-labels.md`
- `docs/skills/blue-team-suricata-multi-iface-capture.md`
- Day 21 / Day 22 challenge tracker entries
