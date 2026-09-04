---
name: Suricata Multi-Iface Lab Capture
description: Capture Athena→host traffic on Rancher Desktop by sniffing eth0 + vznat + cni0, not eth0 alone
tags: [blue-team, suricata, rancher, detection, athena]
inclusion: manual
---

## When to Apply
- Suricata DaemonSet shows zero alerts for in-cluster probes to `host.docker.internal`
- Day 21+ Juice Shop / Night Quire stimulation from a k8s Job
- Rancher Desktop / lima node with `vznat` interface

## Approach
1. Confirm Suricata `hostNetwork: true` and list node ifaces (`ip -br a` in the pod).
2. Pod → host published ports usually traverse **vznat**, not only `eth0`.
3. Start Suricata with every lab iface that exists: `eth0`, `vznat`, `cni0` (skip missing).
4. Expand `HTTP_PORTS` for the published target port (Juice Shop often `:3003` if `:3001` is taken).
5. Probe from an in-cluster Job with `X-Athena-*` headers; verify `eve.json` SIDs on `cni0`/`eth0`.

## Key Patterns
- DaemonSet command builds `-i` list dynamically
- Day 21: `scripts/day21-juice-sqli-suricata.sh` + `scripts/day21-sqli-probe.sh`
- Athena SIDs 20261601–20261603 in ConfigMap `athena.rules`

## Pitfalls
- Host `localhost` curl never hits Suricata — always probe via shared path
- Unquoted curl `-H` values break Job shells — mount a script ConfigMap
- Login SQLi in JSON body is **not** matched by URI-only SID 20261603 (Day 22)

## References
- `deploy/kubernetes/system/suricata/`
- `docs/decisions/0007-hybrid-sensor-suricata.md`
