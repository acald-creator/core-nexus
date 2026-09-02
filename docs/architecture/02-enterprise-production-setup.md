# Enterprise Production Setup: Underground Nexus

This document describes the production architecture direction before introducing UDS as an additional deployment option. The goal is to evolve Underground Nexus from a Docker-focused lab into an enterprise-style Kubernetes platform using Infrastructure as Code, GitOps, and stronger operational controls.

UDS/Zarf can later package and deliver this same architecture for air-gapped or hardened environments. In that model, UDS is a delivery and platform baseline option rather than a contradiction of Kubernetes.

## 1. Production Architectural Shifts

| Lab environment | Production environment | Security+ SY0-701 alignment |
| --- | --- | --- |
| Go script and k3d | Pulumi with Python | **Domains 3.1 and 4.7:** Infrastructure as Code declares cloud infrastructure state, reduces configuration drift, and allows testing of infrastructure logic. |
| Docker Compose | Kubernetes manifests | **Domain 3.4:** Kubernetes provides resilience and self-healing. If a container crashes, Kubernetes can restart it automatically. |
| Local host volumes | Kubernetes volumes, including `emptyDir` where appropriate | **Domain 3.2:** Ephemeral memory-backed volumes can keep selected transient logs off the host disk. Persistent data still needs explicit storage and retention design. |
| Portainer manual UI | Argo CD + Flux GitOps | **Domain 1.3:** Production changes are made through reviewed Git commits instead of manual UI clicks. |
| Vault dev mode | Vault HA with auto-unseal (`nexus-hashistack` / shared) | **Domain 1.4:** Vault can run in high availability mode and use a KMS-backed auto-unseal workflow. |
| MinIO lab buckets | Cloudflare R2 (blobs) + D1 (metadata) | **Domain 3.2 / supply chain:** Durable artifact store with queryable provenance indexes. |

## 2. Secrets and Secure Software Factory Alignment

Vault should remain the primary candidate for secrets management because the broader secure software factory direction is loosely based on FRSCA. In that model, Vault supports build and runtime trust boundaries rather than acting as a generic password bucket.

Recommended responsibilities:

- Store or broker access to signing material for Cosign, attestations, and SBOM workflows.
- Store registry credentials, deployment credentials, and automation tokens.
- Support Kubernetes workloads through secret injection or synchronization.
- Keep build pipeline secrets separate from runtime application secrets.
- Support HA and auto-unseal for production-like deployments.

This keeps the design close to FRSCA-style supply-chain patterns while still allowing GitHub OIDC or keyless signing where appropriate.

## 3. Deployment Options

Underground Nexus can support multiple deployment methods during the transition.

| Option | Role |
| --- | --- |
| Docker Compose / Docker scripts | Current lab deployment path and quick local validation. |
| Kubernetes manifests | Production-style workload definitions and portability layer. |
| Flux CD + Argo CD | **Default programmatic fabric:** Flux for sync/image automation; Argo CD for app delivery and governance. |
| Pulumi | Optional infrastructure provisioning (cloud accounts, clusters) — not a GitOps substitute. |
| UDS / Zarf | Air-gapped delivery, baseline platform services, and packaged deployment option. |
| Object store | MinIO in lab; Cloudflare R2 + D1 in production (S3-shaped app interface). |

## 4. Kubernetes Sidecar Pattern

Kubernetes introduces the sidecar pattern for tightly coupled containers.

In Kubernetes, the smallest deployable unit is a Pod. A Pod can contain multiple containers that share the same local network namespace and storage volumes.

One proposed experimental pattern is to place a Suricata sensor container and an AI triage container in the same Pod while keeping them as separate logical components:

```mermaid
graph TD
    A[Suricata Sensor Container] --> B[Shared emptyDir Volume]
    B --> C[Python AI Triage Container]
    C --> D[Structured JSON Output]
    D --> E[Log or SIEM Pipeline]
```

In this pattern, Suricata writes `eve.json` events to a shared memory-backed `emptyDir`, and the Python AI script reads those events locally. If the Pod is deleted, the shared memory volume disappears with it.

Important caveat: this only controls the lifecycle of the shared handoff volume. Container logs, SIEM events, node logs, crash dumps, and persisted observability data still need separate retention and protection policies.

### 5. DevSecOps Pipeline (Flux CD + Argo CD GitOps)

**Locked default:** Underground Nexus uses **Flux CD and Argo CD together** as the programmable fabric + factory delivery loop (not Portainer, not webtop-driven deploys).

**Bootstrap sketch:** `deploy/gitops/` — Argo owns Application sync; Flux owns image-reflector + image-automation only (no competing Flux Kustomizations). Lab Console + gateway: `deploy/kubernetes/soc/overlays/r2`. Range: `overlays/gitops-range`. MinIO-era pins: `overlays/gitops-lab`. SSF OCI wiring: `deploy/gitops/ssf-follow-on.md`. ADR 0003.

* **Flux CD (Image Automation)**: Watches published `phoenixvlabs/nexus-*` images, updates Git pins via ImageUpdateAutomation.
* **Argo CD (Governance & visualization)**: Primary deployment orchestrator and dashboard. Syncs kustomize overlays for Console, gateway, workbench, Athena, and related SOC paths. Does **not** deploy Vault from this repo (ADR 0008). Inflates Helm only where overlays still declare charts (e.g. optional object-store lab paths).

Secure software factory CI feeds signed images into this loop. **Default factory tool:** [`nebucloud/ssf`](https://github.com/nebucloud/ssf) + [kiln](https://github.com/nebucloud/kiln) (ADR 0004). Flux Image Automation / Argo then promote verified tags. Do not stand up a second Cosign/SBOM stack inside `core-nexus` unless SSF cannot cover the artifact type.

The older `nebucloud/secure-software-factory` monorepo (Fabric/xDS-oriented) is not the active Nexus factory default.

```mermaid
flowchart TD
    subgraph "Secure Software Factory"
        A[GitHub / kiln] -->|Push Changes| B[GitHub Code Repo]
        B -->|Trigger Build| C[CI Registry: phoenixvlabs/nexus-*]
    end

    subgraph "GitOps Control Loop"
        D[Flux CD] -->|1. Detects New Images| C
        D -->|2. Commits Tag Updates| B
        E[Argo CD] -->|3. Tracks Manifests| B
        E -->|4. Syncs State| F[Kubernetes Cluster]
    end

    F -->|5. Deploys Workloads| G[SOC Console Gateway Workbench Athena]
```

### Developer workspace: Jupyter purple workbench
* **Role**: Containerized JupyterLab workspace (`platform/workbench`) with analysis libraries, `hvac` for secrets, and Git tooling — not a full Linux desktop.
* **Security+ alignment**: **Domain 4.1, Secure Baselines.**

### Version Control: GitHub
* **Role**: The source of truth for infrastructure manifests, deployment configurations, model parameters, and policies.
* **Security+ alignment**: **Domain 1.3, Change Management.** Audit trails, pull requests, and cryptographic commit signatures verify authorship.

### Continuous Deployment & Sync (Flux + Argo)
* **Role**: Automated reconcilers keeping the cluster state matching the Git repository.
* **Security+ alignment**: **Domain 4.7, Automation and Orchestration.** No human has direct write access to cluster production APIs; changes are applied by audited, automated service accounts.

---

## 6. Kubernetes Workload DOs and DON'Ts

The following guidelines outline non-negotiable workload security practices for deploying pods in the SOC environment:

### DOs
* **DO use minimal, hardened base images**: Build custom workbench and triage containers using verified secure bases (e.g., `cgr.dev/chainguard/python:latest-dev` for JupyterLab, `python:3.10-slim` for inference APIs) to **reduce** the cluster CVE surface.
* **DO run workloads as non-root users**: Enforce non-root execution inside pod specifications (e.g. running the JupyterLab workbench under user `65532` and standard Athena pods under user `1000`).
* **DO request minimal Linux capabilities**: Only add specific privileges needed by a container (e.g., `capabilities.add: ["NET_ADMIN", "NET_RAW"]` for packet capture in the elevated `nexus-athena-elevated` pod, or `IPC_LOCK` for Vault memory locking).
* **DO manage secrets centrally via HashiCorp Vault**: Read and write credentials programmatically using Vault APIs (e.g. `hvac` Python client) or Vault agent sidecar injectors. 
* **DO label test namespaces/pods to bypass Zarf webhook**: Add `zarf.dev/agent: skip` to namespace or pod metadata during local development to prevent the Zarf agent from hijacking public image pulls.
* **DO enforce directory permissions for non-root volumes**: Use `securityContext.fsGroup` matching the container user (e.g., `65532` or `1000`) to guarantee that mounted PersistentVolumes are writable by non-root containers.
* **DO disable privilege escalation explicitly**: Always set container-level `securityContext.allowPrivilegeEscalation: false` in all container specifications to block processes from utilizing setuid/setgid binaries to escalate privileges.

### DON'Ts
* **DON'T mount the host Docker socket (`/var/run/docker.sock`) by default**: Console, Jupyter workbench, database indices, and triage APIs must run with absolute socket isolation. Only mount the docker socket on explicitly approved, elevated testing profiles in isolated namespaces.
* **DON'T run workloads in privileged mode (`privileged: true`) by default**: Always set `privileged: false` and `allowPrivilegeEscalation: false` for all baseline SOC and triage applications.
* **DON'T store plaintext secrets in git**: Credentials, API tokens, and private keys must never be committed to Git repositories. Utilize Vault or sealed secret wrappers.
* **DON'T colocate network sensor binaries (like Suricata) inside a desktop workspace**: Run packet sniffers as DaemonSets, sidecars, or dedicated capture pods (ADR 0007), sharing alerts through volumes or structured logging — not webtop images.
* **DON'T allow unrestricted cross-namespace communication**: Restrict network traffic using `NetworkPolicies` so that test attacker workloads (Athena) cannot access admin panels or indices directly.

---

## 7. Relationship to UDS

UDS does not replace the Kubernetes architecture. It packages and hardens it.

In a UDS-based deployment:

- Zarf packages the application and dependencies for connected or air-gapped delivery.
  - **Local/Development Workloads and the Zarf Webhook**: When deploying external, non-packaged services to a cluster running Zarf, the Zarf Mutating Admission Webhook will automatically intercept Pod creation and rewrite image URLs to point to the local Zarf registry. To allow public image pulls or bypass this mutator, the namespace or pod must be labeled with `zarf.dev/agent: skip` or `zarf.dev/agent: ignore`.
- UDS Core can provide baseline services such as Authservice for SSO flows, Istio for service mesh networking, Grafana and Prometheus for observability, Loki and Vector for logging, Tetragon for runtime security, and Velero for backup.
- The same Kubernetes workload boundaries still matter: SOC, Athena, Workbench, and AI triage should remain separate logical components, even when an experiment colocates tightly coupled containers in one Pod.
- Secrets remain a separate design decision. Vault HA or another secret manager should be chosen explicitly instead of treating UDS itself as the secrets backend.

---

## 8. Open Planning Questions

- Which services remain in the Docker lab profile and which move first to Kubernetes?
- Does Pulumi provision only infrastructure, or does it also install platform services?
- Does Argo CD remain part of the UDS deployment, or does Zarf handle initial delivery with GitOps added afterward?
- Where does Suricata capture traffic in Docker, Kubernetes, and Istio mTLS environments?
- ~~Is Wazuh the primary security event store, with Loki used for platform logs, or should Vector fan out events to both?~~ **Resolved (ADR 0011):** Wazuh indexer is the full-SIEM store (`overlays/test`); compose-your-own labs use Vector → ai-inference without Wazuh; Loki remains for platform logs.
- Which secrets move from development defaults into Vault HA or another selected secrets manager?
