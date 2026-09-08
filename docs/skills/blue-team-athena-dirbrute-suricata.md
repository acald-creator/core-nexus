---
name: Athena Dir-Bruteforce Suricata Detection
description: Verify Suricata catches Athena dir-bruteforce traffic (Day 24 SIDs, multi-iface probe)
tags: [blue-team, suricata, athena, directory-bruteforce, detection]
inclusion: manual
---

## When to Apply
- Day 24-style Use: run dir discovery and confirm eve.json
- Adding SIDs for `athena-agents/dir-bruteforce` UA or sensitive paths
- Debugging why host-native tool runs produce no Suricata alerts

## Approach
1. Apply SIDs **20262401–203** in `athena.rules` (UA, `/.git`, `/wp-admin`).
2. Local tool invoke proves `dir_bruteforce.py` (host path — Suricata may miss).
3. In-cluster Job → `host.docker.internal:3003` with same UA + Athena headers (capture path).
4. Wait ~25s after Suricata restart before probing.
5. Assert all three Day 24 SIDs in `eve.json`.

## Key Patterns
- Script: `scripts/day24-dir-bruteforce-suricata.sh`
- Probe: `scripts/day24-dirbrute-probe.sh`
- Juice Shop lab port **3003** (3001 often occupied)

## Pitfalls
- Host-only curls never cross vznat — zero alerts despite tool success
- Juice Shop SPA returns **200** for many missing paths (FP fuel for Day 25)
- SID 20262401 fires once per GET — expect high volume on wordlist storms

## References
- `docs/skills/red-team-athena-dir-bruteforce.md`
- `docs/skills/blue-team-suricata-multi-iface-capture.md`
