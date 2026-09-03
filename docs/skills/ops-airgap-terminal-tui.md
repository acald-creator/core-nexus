---
name: Air-gapped Terminal Operator
description: Run Athena labeled traffic and monitor with nexus-tui only — no Console; Zarf for delivery
tags: [ops, air-gap, zarf, uds, nexus-tui, athena]
inclusion: manual
---

## When to Apply
- Day 19-style “agent + monitor from terminal only”
- SSH or air-gapped labs where the browser Console is unavailable
- Packaging operator tools with Zarf (`nexus-airgap-ops`)

## Approach
1. Treat **UDS/Zarf as delivery**, Vault as secrets, Flux/Argo as connected drift — do not conflate them.
2. Operator path: `labeled-probe-session.py` (or OPAR) → JSONL → `nexus-tui`. No Gateway login, no Console port-forward.
3. Use `nexus-tui --dump` for a non-TTY proof (CI, scripts). Interactive TUI is optional.
4. Build media with `deploy/uds/create-packages.sh`. Image tarballs need a connected builder (`ZARF_CREATE_IMAGES=1`).
5. Deploy order if using Zarf on the cluster: platform → hybrid-sensor. airgap-ops is files on the operator host.

## Key Patterns
- `scripts/day19-airgap-terminal.sh`
- `NEXUS_AGENT_LOG` / `NEXUS_ALERTS_FILE` / `NEXUS_SKILLS_DIR`
- Packages: `deploy/uds/nexus-platform`, `nexus-hybrid-sensor`, `nexus-airgap-ops`

## Pitfalls
- Host-native probes still may miss Suricata capture (same as Day 14)
- `zarf package create` for sensors pulls large Helm/images — do not block the Use-day on that
- HTTP JWT middleware does not apply to this path — there is no Console session

## References
- `deploy/uds/README.md`
- `docs/architecture/02-enterprise-production-setup.md` §7
- `cmd/nexus-tui`
