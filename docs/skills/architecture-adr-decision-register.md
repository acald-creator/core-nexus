---
name: Architecture ADR Decision Register
description: Load and apply Underground Nexus Architecture Decision Records when making architecture, GitOps, factory, or deploy choices; use for agent memory of locked defaults
tags: [architecture, adr, decisions, documentation, agent-memory]
inclusion: manual
---

## When to Apply

- Choosing GitOps, Vault, object store, factory, sensor, or client-surface defaults
- Editing architecture docs, README, AGENTS, or deploy/gitops prose
- Resolving contradictions between older docs and the locked product spine
- Planning agent/tooling memory: durable facts live in ADRs, not chat

## Approach

1. Read `docs/decisions/README.md` for the index of Accepted ADRs.
2. Open the relevant ADR (`0002`–`0008`) before changing related docs or manifests.
3. Cross-check `docs/architecture/01-component-architecture.md` §0 (product narrative).
4. Update the ADR if the decision changes; do not silently override in a random doc.
5. Prefer one-line consequences in PRs: “per ADR 0003, Argo path remains overlays/r2.”

## Key Patterns

| Concern | ADR |
| --- | --- |
| Fabric + factory + range | 0002 |
| Flux + Argo (r2 / gitops-range) | 0003 |
| ssf + kiln (no Cosign dupe) | 0004 |
| MinIO lab / R2+D1 prod | 0005 |
| Console, Jupyter, Athena; webtops retired | 0006 |
| Suricata hybrid sensor (still in plan) | 0007 |
| Vault via nexus-hashistack | 0008 |
| Lab-only Portainer / no Vault-in-core-nexus | 0001 + 0008 |

ADR shape: Status → Context → Decision → Consequences.

## Pitfalls

- Do not treat `overlays/gitops-lab` as the live Argo lab app (that is `overlays/r2`).
- Do not drop Suricata from the cybersecurity plan because the thin spine omits it.
- Do not map athena-agents OPAR to architecture Phase 2/3 SecureOS — OPAR is Phase 1 capable.
- Do not invent a second factory stack inside core-nexus.

## References

- `docs/decisions/`
- `docs/architecture/01-component-architecture.md` §0
- `docs/00-ai-collaboration.md` §3–4, §7
- `deploy/gitops/README.md`
- `scripts/sync-skills.sh` (push this skill to `~/.kiro/skills/` / object store when wiring agent memory)
