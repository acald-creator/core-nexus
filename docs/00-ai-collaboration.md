# AI Collaboration Guide

This repository is designed to be worked on by multiple AI assistants, including Codex, Claude, and Gemini. The goal is not to make the models compete, but to use each one for the type of work it handles well while keeping architecture decisions consistent.

## 1. Canonical Architecture Documents

Use these documents as the source of truth, in order:

| Order | Document | Purpose |
| --- | --- | --- |
| 1 | `docs/architecture/01-component-architecture.md` | Current component map and practical target architecture |
| 2 | `docs/architecture/02-enterprise-production-setup.md` | Kubernetes, Pulumi, Argo CD, UDS/Zarf production bridge |
| 3 | `docs/architecture/03-phased-implementation-roadmap.md` | Phase 1 through Phase 3 maturity model |
| 4 | `docs/architecture/04-ai-native-enterprise platform-proposal.md` | Long-horizon Enterprise Platform/SecureOS concept |
| 5 | `docs/architecture/05-sensor-deep-dive.md` | Hybrid Suricata plus runtime telemetry sensor |
| 6 | `docs/architecture/06-ai-soc-inference-engine.md` | AI triage and model governance |
| 7 | `docs/architecture/07-mcp-workbench.md` | Nexus MCP server and purple-team MLOps workbench |
| 8 | `docs/architecture/08-athena-adversary-fuzzer.md` | Controlled adversarial data generation |
| 9 | `docs/architecture/09-production-deployment-lifecycle.md` | Future Enterprise Platform bare-metal lifecycle |
| 10 | `docs/architecture/10-ai-infused-security-plus-labs.md` | Security+ lab scenarios |
| 11 | `docs/architecture/11-ai-native-integration-principles.md` | AI-native design and integration principles |
| 12 | `docs/architecture/12-vault-environments-specification.md` | Dev, Test, and Prod Vault environments |

When documents conflict, prefer the lower-numbered practical architecture documents for near-term implementation and the higher-numbered Enterprise Platform documents for future-state concepts.

## 2. Model Roles

| Model | Best use | Expected output |
| --- | --- | --- |
| Codex | Repo edits, code changes, consistency passes, implementation planning | Concrete file changes, patches, verification notes |
| Claude | Long-form architecture critique, risk analysis, narrative refinement | Review notes, alternative architectures, threat-model questions |
| Gemini | Broad research synthesis, comparison, product/platform option review | Research summaries, tradeoff tables, external landscape notes |

These roles are defaults, not hard rules. Any model may review any document, but it should respect the repository vocabulary and decision register.

## 3. Shared Vocabulary

- **Underground Nexus:** Security lab, SOC, AI triage, and adversarial validation environment.
- **Enterprise Platform:** Broader platform that may eventually provide compute, identity, control-plane, and execution boundaries.
- **Platform UI:** AI-enabled visual website/workload. It is not the destination for Nexus threat findings.
- **SecureOS:** Long-horizon OS target. It is not assumed ready for current workloads.
- **gVisor:** Hermetic execution target. Its exact runtime role should be clarified before implementation.
- **Control Plane:** Rust xDS control-plane server. Data-plane APIs perform runtime changes.
- **Hybrid sensor:** Suricata for network/protocol telemetry plus runtime or kernel telemetry.
- **Nexus MCP Server:** Interface layer for approved SOC/Nexus tools and context.
- **Kubernetes production model:** Near-term production-like path using Kubernetes, Pulumi, Argo CD, and optionally UDS/Zarf.
- **Future Enterprise Platform bare-metal production:** Long-horizon SecureOS, Control Plane, and gVisor deployment lifecycle.

## 4. Non-Negotiable Architecture Decisions

- Suricata becomes the network/protocol side of the hybrid sensor.
- Runtime or kernel telemetry complements Suricata; it does not automatically replace it.
- Wazuh is the near-term SOC event store.
- Loki is for platform and workload logs.
- MinIO is for artifacts, evidence, datasets, backups, and package archives.
- Vault is the preferred production-like secrets manager; UDS is not the secrets backend.
- Platform UI is monitored like any other workload, but threat findings go to approved Nexus/SOC clients.
- Autonomous response is a later capability. Human approval and auditability come first.
- Cloudflare-to-SecureOS deployment is a future Enterprise Platform bare-metal lifecycle, not the current Kubernetes/UDS path.

## 5. Review Protocol

When an AI model reviews or edits this repo:

1. Identify which phase the change affects:
   - Phase 1: current Linux/Docker/Kubernetes bridge
   - Phase 2: hermetic migration
   - Phase 3: high-assurance Enterprise Platform target
2. State whether the change is documentation-only, planning, or implementation.
3. Check for terminology consistency:
   - Platform UI vs Enterprise Platform
   - Control Plane control plane vs data-plane APIs
   - Suricata as hybrid sensor component
   - Kubernetes production vs future Enterprise Platform bare-metal production
4. Avoid overstated claims:
   - No “tamper-proof” without a defined verification model.
   - No “zero-day detection” without evaluation evidence.
   - No autonomous response without policy, identity, and audit controls.
5. Leave a short verification note after changes.

## 6. Suggested Prompt Templates

### Discrepancy Review

```text
Review the numbered Markdown documents in this repository.
Find contradictions, terminology drift, phase mismatches, overstated security claims, and broken conceptual links.
Return file and line references. Do not edit files.
```

### Architecture Refinement

```text
Refine the architecture docs for consistency with these decisions:
Suricata is part of the hybrid sensor, Control Plane is the Rust xDS control-plane server, Platform UI is not a SOC findings destination, and Kubernetes production is separate from future Enterprise Platform bare-metal production.
Edit files directly and summarize changes.
```

### Implementation Planning

```text
Create a Phase 1 implementation plan that preserves the current Docker lab while moving toward Wazuh, hybrid Suricata/runtime sensing, Vault HA, MinIO artifact storage, and AI triage enrichment.
Keep Phase 2 and Phase 3 items explicitly out of scope.
```

## 7. Handoff Format

When one model hands work to another, use this format:

```text
Context:
- Phase:
- Files touched:
- Decisions made:
- Open questions:
- Verification performed:
- Recommended next action:
```
