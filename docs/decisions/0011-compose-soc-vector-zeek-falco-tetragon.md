# Compose-Your-Own SOC: Vector + Zeek / Falco / Tetragon

## Status

Accepted

## Context

Underground Nexus locked **Wazuh** as the near-term SOC event store (`docs/00-ai-collaboration.md`
§4) and **Suricata** as the network IDS side of the hybrid sensor (ADR 0007). The thin GitOps
lab overlay (`overlays/r2`) deliberately omits Wazuh and heavy sensors to save RAM.

Operators want a **compose-your-own** security telemetry path using tools already planned or
vendored in-repo:

| Tool | Role |
| --- | --- |
| **Vector** | Collect, normalize, route (`deploy/kubernetes/system/vector`) |
| **Suricata** | Signature IDS, `eve.json` (ADR 0007) |
| **Zeek** | Network metadata / protocol analysis (arch `01` optional sensor) |
| **Falco** | Runtime threat rules (containers / K8s audit) |
| **Tetragon** | eBPF runtime telemetry (Cilium ecosystem) |

Wazuh remains available in `overlays/test` and `wazuh-secure` for full SIEM labs. It is **not**
required for ai-inference triage or Console deep-links when events are ingested via Vector →
`POST /v1/triage`.

## Decision

### Default lab profiles

| Overlay | SOC store | Sensors | Use when |
| --- | --- | --- | --- |
| `overlays/r2` | None (triage API only) | None | Thin Console + gateway + ai-inference |
| **`overlays/hybrid-sensor`** | Vector → ai-inference (+ optional Loki) | Suricata, Zeek, Falco, Tetragon, Vector | Compose-your-own SOC without Wazuh |
| `overlays/test` | Wazuh indexer | Suricata, Tetragon, Vector, Kyverno | Full integration test / Wazuh path |

### Sensor division of labor

- **Suricata** — IDS alerts and Athena signature-coverage exercises (ADR 0007 unchanged).
- **Zeek** — conn/DNS/HTTP metadata and purple-team timelines; complements Suricata.
- **Falco** — primary **alerting** runtime detector (portable rules, lower ops burden).
- **Tetragon** — deep eBPF export for kernel-level ground truth; feeds Vector, not duplicate Falco rules by default.

### Vector as integration bus

All hybrid sensors emit to **Vector** (DaemonSet agent in `kube-system`). Vector:

1. Tags events with `nexus.source` ∈ `{suricata, zeek, falco, tetragon}`.
2. Remaps to a **normalized JSON** shape compatible with `platform/ai-inference` triage v1.1+.
3. **Sinks:**
   - `http://ai-inference.soc.svc.cluster.local:8000/v1/triage` — scoring + SQLite persistence (required).
   - Loki or OpenSearch — optional investigation store (later); not required for thin lab.
4. **Does not** require Wazuh indexer when hybrid overlay is used.

Wazuh elasticsearch sink in `vector-values.yaml` is **legacy / test overlay only**; hybrid uses
`vector-values-hybrid.yaml`.

### Gateway and Console

- **Triage deep-link:** `GET /api/v1/alerts/{id}/triage` — unchanged; reads ai-inference persistence.
- **Alert list:** Wazuh API remains the default adapter when Wazuh is deployed. Hybrid labs without
  Wazuh use direct triage POST or a follow-on **SOC events adapter** (OpenSearch/Loki query) — not
  blocking hybrid-sensor v1.
- Console Approvals and factory review (ADR 0009) are independent of Wazuh.

### Athena / labeled traffic

Labeled stimulation traffic (headers + env) must remain distinguishable in normalized events
(`X-Athena-Scenario`, `nexus.athena_scenario`) so triage and purple eval can prefer
`needs_human_review` over auto-contain language.

### Phased delivery

| Phase | Intent |
| --- | --- |
| H0 | This ADR + `overlays/hybrid-sensor` + system charts (Falco, Zeek) |
| H1 | Vector hybrid pipeline → ai-inference; lab README |
| H2 | Gateway `SOCEvent` adapter (Loki/OpenSearch or in-memory recent buffer) |
| H3 | Triage feature pack extensions for Zeek/Falco-specific fields |
| H4 | Purple eval: ground-truth ↔ Zeek conn + Falco + Suricata correlation |

## Consequences

- Wazuh is **a profile**, not the only SOC path; `00-ai-collaboration.md` non-negotiable updated
  to list hybrid compose as an accepted lab default alongside Wazuh near-term store.
- ADR 0007 unchanged: Suricata stays in the cybersecurity plan; Zeek adds metadata, does not replace it.
- `overlays/r2` stays thin; operators who want sensors apply `hybrid-sensor` (or `test` for Wazuh).
- RAM: hybrid-sensor is heavier than r2; Rancher Desktop ≥8 Gi recommended when Falco + Zeek + Suricata run together.
- New manifests live under `deploy/kubernetes/system/{falco,zeek}` and `deploy/kubernetes/soc/overlays/hybrid-sensor`.
- Gateway Wazuh client remains for Wazuh deployments; hybrid labs are not broken when Wazuh is absent.

## References

- ADR 0007 (Suricata hybrid sensor)
- `docs/architecture/01-component-architecture.md` §4 (event/logging architecture)
- `deploy/kubernetes/soc/overlays/hybrid-sensor/vector/vector-values-hybrid.yaml`
- `deploy/kubernetes/soc/overlays/hybrid-sensor/README.md`
