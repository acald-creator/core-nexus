# Product Spine: Fabric + Factory + Range

## Status

Accepted

## Context

Underground Nexus had accumulated desktop webtops, Portainer-centric ops, and
overlapping “platform” narratives (Enterprise Platform / SecureOS) that blurred
what the product is *now* versus long-horizon research.

## Decision

Underground Nexus is a **programmable fabric** plus a **secure software factory**,
with an attached **red / blue / purple range**.

| Plane | Purpose |
| --- | --- |
| Fabric | Deployable components, namespaces, identity, secrets, observability |
| Secure software factory | Build → SBOM → sign → attest → promote |
| Blue | SOC detection and ops UX |
| Purple | Evaluate detections / models against ground truth |
| Red | Controlled stimulation / emulation |

Near-term Kubernetes / Docker / GitOps work stays on this spine. Enterprise
Platform / SecureOS / bare-metal lifecycle docs (`04`, `09`) remain future-state
and must not redefine Phase 1 defaults.

Canonical narrative: `docs/architecture/01-component-architecture.md` §0.

## Consequences

- READMEs, GitOps sketches, and agent instructions describe the three planes explicitly.
- Phase 1 roadmap centers fabric + factory + range — not SecureOS hosting Nexus.
- New features map to a plane (or are rejected as out of spine).
