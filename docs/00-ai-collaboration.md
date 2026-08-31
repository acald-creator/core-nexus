# AI Collaboration Guide

This repository is designed to be worked on by multiple AI assistants, including Codex, Claude, and Gemini. The goal is not to make the models compete, but to use each one for the type of work it handles well while keeping architecture decisions consistent.

## 1. Canonical Architecture Documents

Use these documents as the source of truth, in order:

| Order | Document | Purpose |
| --- | --- | --- |
| 1 | `docs/architecture/01-component-architecture.md` | Current component map and practical target architecture |
| 2 | `docs/architecture/02-enterprise-production-setup.md` | Kubernetes, Pulumi, Flux + Argo CD, UDS/Zarf production bridge |
| 3 | `docs/architecture/03-phased-implementation-roadmap.md` | Phase 1 through Phase 3 maturity model |
| 4 | `docs/architecture/04-ai-native-platform-proposal.md` | Long-horizon Enterprise Platform/SecureOS concept |
| 5 | `docs/architecture/05-sensor-deep-dive.md` | Hybrid Suricata plus runtime telemetry sensor |
| 6 | `docs/architecture/06-ai-soc-inference-engine.md` | AI triage and model governance |
| 7 | `docs/architecture/07-mcp-workbench.md` | Nexus MCP server and purple-team MLOps workbench |
| 8 | `docs/architecture/08-athena-adversary-fuzzer.md` | Controlled adversarial data generation |
| 9 | `docs/architecture/09-production-deployment-lifecycle.md` | Future Enterprise Platform bare-metal lifecycle |
| 10 | `docs/architecture/10-ai-infused-security-plus-labs.md` | Security+ lab scenarios |
| 11 | `docs/architecture/11-ai-native-integration-principles.md` | AI-native design and integration principles |
| 12 | `docs/architecture/12-vault-environments-specification.md` | Vault intent (runtime in nexus-hashistack) |
| 13 | `docs/architecture/13-agent-workflows-and-memory.md` | OPAR, skills, nexus-tui, safety controls |
| — | `docs/decisions/` | Architecture Decision Records (locked defaults) |

When documents conflict, prefer the lower-numbered practical architecture documents and **Accepted ADRs** for near-term implementation; prefer higher-numbered Enterprise Platform documents for future-state concepts only.

## 2. Model Roles

| Model | Best use | Expected output |
| --- | --- | --- |
| Codex | Repo edits, code changes, consistency passes, implementation planning | Concrete file changes, patches, verification notes |
| Claude | Long-form architecture critique, risk analysis, narrative refinement | Review notes, alternative architectures, threat-model questions |
| Gemini | Broad research synthesis, comparison, product/platform option review | Research summaries, tradeoff tables, external landscape notes |
| Kiro | IDE-integrated implementation, spec-driven development, skill-driven workflows | File edits, hook/steering configs, auto-generated skills |
| LLM Agents (runtime) | Autonomous adversary emulation, SOC stimulation, OPAR execution loops | Ground-truth telemetry, attack traffic, coverage metrics, skill files |

These roles are defaults, not hard rules. Any model may review any document, but it should respect the repository vocabulary and decision register.

**Note on LLM agents as runtime components:** Unlike the development-time models above, LLM agents also operate as platform runtime components within the Athena environment (`athena-agents`). They autonomously plan and execute attack scenarios, emit labeled ground-truth data, and build persistent skill memory. See `docs/architecture/11-ai-native-integration-principles.md` Section 4 and `docs/architecture/08-athena-adversary-fuzzer.md` Section 8 for the full architecture.

## 3. Shared Vocabulary

- **Underground Nexus:** Programmable fabric + secure software factory with an attached red/blue/purple range (cybersecurity lab, SOC, AI triage, adversarial validation).
- **Fabric:** Deployable components, namespaces, identity, secrets, observability (Kubernetes overlays, Vault via hashistack, GitOps).
- **Secure software factory:** Build → SBOM → sign → attest → promote via `nebucloud/ssf` + kiln, then Flux/Argo promotion.
- **Enterprise Platform:** Broader platform that may eventually provide compute, identity, control-plane, and execution boundaries (future).
- **Platform UI:** AI-enabled visual website/workload. It is not the destination for Nexus threat findings.
- **SecureOS:** Long-horizon OS target. It is not assumed ready for current workloads.
- **gVisor:** Hermetic execution target. Its exact runtime role should be clarified before implementation.
- **Control Plane:** Rust xDS control-plane server. Data-plane APIs perform runtime changes.
- **Hybrid sensor:** Suricata for network/protocol telemetry plus runtime or kernel telemetry (Suricata is not optional for the cybersecurity plan).
- **Nexus MCP Server:** Interface layer for approved SOC/Nexus tools and context.
- **Kubernetes production model:** Near-term production-like path using Kubernetes, Pulumi, **Flux + Argo CD**, and optionally UDS/Zarf.
- **Future Enterprise Platform bare-metal production:** Long-horizon SecureOS, Control Plane, and gVisor deployment lifecycle.
- **OPAR loop:** Observe/Plan/Act/Reflect execution cycle used by LLM agents for autonomous offensive testing. Implemented in `athena-agents` (Phase 1 capable).
- **Stimulation:** LLM agents generating adaptive, labeled attack traffic against approved targets to exercise detection coverage.
- **Emulation:** LLM agents assuming adversary roles, reasoning through multi-step attack chains against sandbox environments.
- **Agent skill:** A persistent, reusable encoding of a proven approach (technique sequence, patterns, pitfalls) that eliminates redundant LLM reasoning on repeat encounters.
- **Ground-truth record:** A labeled telemetry record emitted during agent execution with scenario ID, technique, timestamp, and expected result — used to evaluate SOC detection accuracy.
- **athena-agents:** AI offensive agent framework implementing the OPAR loop with configurable LLM backends, safety controls, and ground-truth emission.
- **ADR:** Architecture Decision Record under `docs/decisions/` — durable locked defaults for agents and humans.

## 4. Non-Negotiable Architecture Decisions

- Suricata is the network/protocol side of the hybrid sensor (ADR 0007); runtime telemetry complements it.
- Wazuh is the near-term SOC event store.
- Loki is for platform and workload logs.
- Object storage: **MinIO in lab**; **Cloudflare R2 + D1 in production-like** paths (ADR 0005).
- Vault is the preferred production-like secrets manager, **owned by nexus-hashistack / shared Vault** — not deployed from core-nexus (ADR 0008).
- GitOps default: **Flux** (image automation) + **Argo CD** (app delivery) (ADR 0003).
- Factory default: **nebucloud/ssf + kiln**; do not duplicate Cosign stacks in core-nexus (ADR 0004).
- Factory AI (secure coding / review): sibling **`nebucloud/factory-agents`**; review-first; kiln is callee for hermetic verify/build — not the agent workspace; do not host coding LLMs in `platform/ai-inference` (ADR 0009).
- Human clients: Nexus Console, Jupyter purple workspace, isolated Athena; webtops retired (ADR 0006).
- Platform UI is monitored like any other workload, but threat findings go to approved Nexus/SOC clients.
- Autonomous response is a later capability. Human approval and auditability come first.
- Cloudflare-to-SecureOS deployment is a future Enterprise Platform bare-metal lifecycle, not the current Kubernetes/UDS path.
- LLM agents operate within allowlist and capability-gate constraints at all times.
- Agent skill persistence uses object store (platform) or local filesystem (development); skills are versioned and signed before unattended use.
- Stimulation and emulation traffic must be labeled (HTTP headers + env vars) so SOC dashboards can distinguish training traffic from real alerts.
- Product spine is fabric + factory + range (ADR 0002); see `01` §0.

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
Create a Phase 1 implementation plan that preserves the current Docker lab while moving toward Wazuh, hybrid Suricata/runtime sensing, Vault via nexus-hashistack, MinIO (lab) / R2+D1 (prod) object storage, Flux+Argo GitOps, and AI triage enrichment.
Keep Phase 2 and Phase 3 items explicitly out of scope.
```

## 7. Cross-Repository Context

| Repository | Role | Key artifacts |
| --- | --- | --- |
| `core-nexus` | Architecture hub, platform definitions, deployment manifests | `docs/architecture/`, `platform/`, `deploy/` |
| `nexus-hashistack` | Local/shared Vault (+ Consul) packs; AppRole export for `--from-vault` | `scripts/`, `docs/nexus-wiring.md` |
| `nexus-athena` | Red-team container image (Kali-based offensive tooling) | `Dockerfile.*`, deploy profiles |
| `athena-agents` | LLM-driven adversary emulation framework (OPAR loop) | `orchestrator/`, `config/`, `eval/` |
| `nexus-webtop-soc` | **Retired** — archive compose only; prefer `deploy/kubernetes/soc/` | do not pull k8s base into core-nexus |
| `nexus-webtop-workbench` | **Retired** analyst desktop; use Jupyter workbench + Console | archive path |

**Keep as human surfaces:** Nexus Console, Jupyter purple workspace, isolated Athena.
**GitOps default:** Flux + Argo CD (ADR 0003). **Prod objects:** Cloudflare R2 + D1 (lab: MinIO) (ADR 0005). **ADRs:** `docs/decisions/`.

When working on LLM agent workflows, the primary implementation lives in `athena-agents`. Architecture and integration docs live in `core-nexus`. The container runtime for agent execution lives in `nexus-athena`.

## 8. Handoff Format

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
