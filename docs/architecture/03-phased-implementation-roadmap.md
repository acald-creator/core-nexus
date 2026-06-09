# Underground Nexus: Phased Implementation Roadmap

Building a from-scratch, high-assurance operating system such as SecureOS is a multi-year engineering effort. To keep Underground Nexus useful during that lifecycle, the Enterprise Platform platform and Nexus security workloads should evolve through phases.

This roadmap connects the current Linux-based bootstrap environment, the practical Kubernetes/UDS architecture, and the long-horizon AI-native Enterprise Platform target state.

## Phase 1: Bootstrap

**Status:** Current state

**Primary goal:** Secure the software supply chain and protect ongoing development of Enterprise Platform, SecureOS, Platform UI, and the secure software factory.

SecureOS is still in early userspace development. It may render early UI elements such as a top bar or terminal, but it is not ready to host the Enterprise Platform control plane or Underground Nexus AI-SOC workloads.

### Architecture

| Area | Phase 1 approach |
| --- | --- |
| Host OS | Hardened standard Linux distribution, such as Alpine or Ubuntu |
| Execution | Docker Compose baseline (Nexus Console, Portainer) + KuberNexus (k3d) for workloads |
| Primary UI | `nexus-console` (Custom React/Vite Launchpad Dashboard) |
| SOC platform | Phase 1 target baseline built: Wazuh, Suricata, MinIO running in KuberNexus (k3d) |
| Workbench | `nexus-workbench` (JupyterLab) providing the unified agentic workspace |
| Athena | `nexus-athena` (Kali Linux build) with standard and elevated profiles |
| Secrets | Vault dev mode for local learning; begin designing Vault HA for production-like paths |
| Supply chain | Cosign, SBOMs, attestations, vulnerability scans, registry controls |

### Underground Nexus Role

Underground Nexus acts as the guardian of the factory. It monitors build servers, artifact pipelines, package outputs, approved test environments, and developer workflow anomalies. Platform UI may be one workload under development, but it is not the destination for Nexus threat findings.

### Security+ Alignment

- **Domain 2.3:** Supply chain vulnerabilities
- **Domain 4.1:** Secure baselines
- **Domain 4.2:** Security monitoring

### Visual Plot

```mermaid
graph TD
    subgraph "Standard Linux Infrastructure (Current Base)"
        A[Hardened Linux OS]
        B[Enterprise Platform SSF and Artifact Pipeline]
        A --> B
    end

    subgraph "Underground Nexus (Guardian)"
        C[Wazuh / Suricata SOC Baseline]
        D[AI Triage Enrichment]
        E[Purple Team Workbench]
        B -->|Telemetry and Build Events| C
        C --> D
    end

    subgraph "Target Platform In Development"
        F[SecureOS Alpha Build]
        G[Early Userspace Milestones]
        F --> G
        E -.->|Compiles and Tests| F
    end

    style A fill:#475569,stroke:#fff
    style C fill:#1e3a8a,stroke:#fff
    style D fill:#0f172a,stroke:#eab308,color:#fff
    style F fill:#0f172a,stroke:#eab308,color:#fff
```

### Exit Criteria

- [x] Current Docker lab profiles are documented.
- [x] SOC baseline exists with Wazuh and Suricata separated from the webtop, running on KuberNexus (k3d).
- [x] Primary UI replaced with Custom Nexus Console Launchpad.
- [ ] Workbench and Athena have standard and elevated runtime profiles.
- [ ] SBOM, signing, vulnerability scanning, and attestation workflows are documented.
- [ ] Vault production direction is selected, even if only dev mode exists locally.

## Phase 2: Hermetic Migration

**Status:** Beta target

**Primary goal:** Move Enterprise Platform control-plane workloads and selected Nexus workloads from standard Linux assumptions toward SecureOS and gVisor.

This phase begins once SecureOS has stable enough networking, process management, and observability hooks to support real workloads or realistic subsystem tests.

### Architecture

| Area | Phase 2 approach |
| --- | --- |
| Host OS | SecureOS for selected workloads; Linux remains available for fallback and comparison |
| Execution | gVisor becomes the preferred hermetic runtime for selected services |
| Telemetry | Early SecureOS tracing, eBPF-like hooks, or equivalent kernel telemetry |
| SOC platform | Wazuh and hybrid Suricata/runtime telemetry remain the known-good detection baseline while AI-native telemetry is validated |
| AI triage | Starts consuming SecureOS telemetry alongside existing SOC events |
| Workbench | Moves toward secured JupyterLab or VS Code Server if Enterprise Platform Auth is ready |
| Athena | Begins moving from Kali container workflows to controlled adversary automation |

### Underground Nexus Role

The AI-SOC starts monitoring early SecureOS telemetry while still relying on Wazuh and Suricata network/protocol telemetry for comparison. The goal is to evolve Suricata into the network side of a hybrid sensor rather than discard it.

### Security+ Alignment

- **Domain 3.1:** Security architecture models
- **Domain 3.2:** Infrastructure considerations
- **Domain 4.7:** Automation and orchestration

### Exit Criteria

- gVisor can execute at least one non-trivial Nexus workload repeatably.
- SecureOS telemetry can be exported in a documented schema.
- AI triage can compare standard SOC events against SecureOS telemetry.
- Workloads have signed artifacts and provenance from the secure software factory.
- Fallback to the Linux/Kubernetes baseline remains available.

## Phase 3: High-Assurance Sovereign Cloud

**Status:** Target state

**Primary goal:** Merge formal verification, hermetic execution, and AI-native security operations.

This is the long-horizon target where SecureOS is mature enough to host Enterprise Platform platform services and Underground Nexus security workloads.

### Architecture

| Area | Phase 3 approach |
| --- | --- |
| Host OS | Mature SecureOS |
| Verification | Kernel verification with tools such as Frama-C; userspace verification with tools such as Creusot where practical |
| Execution | All core workloads run as hermetically sealed gVisor workloads |
| Telemetry | Kernel-native telemetry feeds the AI-SOC inference engine |
| Interface | Nexus MCP server exposes approved tools and context |
| Response | Rust xDS control plane coordinates approved response actions; data-plane APIs perform the runtime changes |

### Visual Plot

```mermaid
graph TD
    subgraph "SecureOS (High-Assurance Foundation)"
        A[Verified Kernel]
        B[gVisor: Hermetic Sandbox]
        A --> B
    end

    subgraph "Enterprise Platform Platform"
        C[Rust xDS Control Plane]
        D[Enterprise Platform Auth and SSF]
        B --> C
        B --> D
    end

    subgraph "Underground Nexus (AI-SOC)"
        E[AI Inference Agent]
        F[Kernel Telemetry Hook]
        G[Nexus MCP Server]
        A -.->|Telemetry| F
        F --> E
        E --> G
        G <-->|Approved Orchestration| C
    end

    style A fill:#047857,stroke:#fff
    style B fill:#047857,stroke:#fff
    style E fill:#0f172a,stroke:#eab308,color:#fff
    style G fill:#3178c6,stroke:#fff
```

### Underground Nexus Role

Underground Nexus becomes the AI-native security subsystem for Enterprise Platform. The AI-SOC consumes kernel-native telemetry, the MCP server exposes approved response tools, and the workbench supports purple-team model refinement.

### Security+ Alignment

- **Domain 3.1:** Security architecture models
- **Domain 3.4:** Resilience and recovery
- **Domain 4.8:** Incident response

### Exit Criteria

- SecureOS can host the Enterprise Platform control plane and selected Nexus workloads.
- gVisor provides stable hermetic execution for production services.
- Kernel telemetry is documented, signed, and resistant to tampering.
- MCP response actions require identity, authorization, and audit trails.
- Model versions, telemetry schemas, training datasets, and inference outputs are signed and traceable.

## Roadmap Guardrails

- Keep Suricata as the network/protocol side of the hybrid sensor while AI-native runtime telemetry matures.
- Keep lab, production, and future Enterprise Platform tracks explicitly separate.
- Treat autonomous response as a later capability; start with human-approved actions.
- Sign and attest model artifacts with the same care as container images.
- Keep Athena-style adversarial generation isolated from production systems.
