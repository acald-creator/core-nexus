# Hybrid Sensor: Suricata + Runtime Telemetry

## Status

Accepted

## Context

Underground Nexus is a cybersecurity lab and SOC path. Network/protocol detection
cannot be dropped in favor of runtime-only or AI-only approaches. Suricata remains
the labeled-traffic and IDS foundation for Athena stimulation → detection coverage.

## Decision

- **Suricata** is the network/protocol side of the **hybrid sensor**.
- Runtime / kernel telemetry (e.g. Tetragon) **complements** Suricata; it does not
  replace it.
- Wazuh is the **full-SIEM** SOC event store (`overlays/test`, `wazuh-secure`). Compose-your-own labs use Vector → ai-inference without Wazuh (ADR 0011, `overlays/hybrid-sensor`).
- Suricata events feed Wazuh, Vector, or ai-inference as routed by overlay profile.
- Suricata runs as a **dedicated sensor image** (DaemonSet / capture path), not
  compiled into a desktop webtop.
- Manifests: `deploy/kubernetes/system/suricata` (included from SOC `overlays/test`,
  `overlays/hybrid-sensor`, and related system charts).

The thin GitOps spine (`overlays/r2`, `gitops-range`) may omit Suricata for RAM /
scope reasons; that is a **lab thinning** choice, not a retirement. Full SOC /
cybersecurity plans still include Suricata.

## Consequences

- Architecture and AI collaboration non-negotiables keep Suricata listed.
- Athena/OPAR ground-truth evaluation assumes Suricata (and Wazuh or hybrid Vector path) can observe
  labeled traffic.
- Capture attachment mode (Docker lab vs k8s DaemonSet/sidecar) remains an open
  engineering decision — existence of Suricata in the plan does not.
