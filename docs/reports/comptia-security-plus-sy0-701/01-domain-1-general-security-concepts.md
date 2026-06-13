# Domain 1.0: General Security Concepts

## 1.1 Compare and contrast various types of security controls

### Categories
- **Technical:** *Security controls implemented through technology (e.g., firewalls, encryption, access control lists).*
  - **Nexus Mapping:** Kyverno (admission control), and Vault (secrets management).
- **Managerial:** *Security controls focused on the management of risk and the governance of information systems (e.g., risk assessments, policies).*
  - **Nexus Mapping:** Managed through GitOps (Argo CD) pipelines, where repository approvals and branch protections act as managerial policy enforcement.
- **Operational:** *Security controls executed by people in their day-to-day operations (e.g., security awareness training, incident response procedures).*
  - **Nexus Mapping:** **[GAP IDENTIFIED]** Core Nexus currently lacks a dedicated operational runbook or incident response workflow platform (the `nexus-workbench` JupyterLab is dedicated to AI/ML work, not SOC operations). This indicates a need for future integration of an operational platform (e.g., dedicated SOAR or ticketing system) for analysts.
- **Physical:** *Security controls designed to protect the physical environment and facilities (e.g., locks, cameras, guards).*
  - **Nexus Mapping:** Inherited from the physical deployment environment (e.g., data center controls, lab room physical security). Outside the direct software stack scope.

### Control Types
- **Preventive:** *Controls designed to stop an incident from occurring.*
  - **Nexus Mapping:** Chainguard hardened images (preventing exploitation of vulnerable packages) and Kyverno admission controls (preventing deployment of non-compliant resources).
- **Deterrent:** *Controls intended to discourage a threat actor from causing an incident.*
  - **Nexus Mapping:** SSH login warning banners for the underlying Kubernetes (K3s/RKE2) host nodes.
- **Detective:** *Controls designed to identify and record that a security incident has occurred.*
  - **Nexus Mapping:** Wazuh agents detecting host-level anomalies and Tetragon detecting anomalous container behavior via eBPF.
- **Corrective:** *Controls designed to mitigate the damage of an incident and restore the system to normal operations.*
  - **Nexus Mapping:** Argo CD's self-healing synchronization, which automatically corrects configuration drift by reverting to the Git source of truth.
- **Compensating:** *Controls implemented to provide an alternative solution when a primary control is not feasible.*
  - **Nexus Mapping:** **[GAP IDENTIFIED]** Without a service mesh (like Istio), there is no centralized ingress proxy to act as a compensating authentication control for legacy applications.
- **Directive:** *Controls that mandate specific actions, rules, or behaviors (often administrative).*
  - **Nexus Mapping:** Repository commit signing requirements and mandatory pull request reviews before Argo CD deploys changes to the cluster.

## 1.2 Summarize fundamental security concepts

### Core Concepts
- **Confidentiality, Integrity, and Availability (CIA):** *Confidentiality (protecting data from unauthorized disclosure), Integrity (protecting data from unauthorized alteration), Availability (ensuring data is accessible when needed).*
  - **Nexus Mapping:** Confidentiality via HashiCorp Vault. Integrity via container image signing (Sigstore/Cosign/Chainguard). Availability via Kubernetes (K3s/RKE2) orchestration and replication.
- **Non-repudiation:** *Ensuring that a party cannot deny the authenticity of their signature on a document or a message that they originated.*
  - **Nexus Mapping:** GitOps repository commit signing (GPG/Sigstore) ensures developers cannot repudiate their configuration changes.
- **Authentication, Authorization, and Accounting (AAA):** *Framework for intelligently controlling access, enforcing policies, and auditing usage.*
  - **Authenticating people:** *Verifying a human user's identity.*
    - **Nexus Mapping:** **[GAP IDENTIFIED]** Since there is no active centralized identity provider in this infrastructure, there is a gap in centralized identity/SSO for human users.
  - **Authenticating systems:** *Verifying a machine or service's identity.*
    - **Nexus Mapping:** **[GAP IDENTIFIED]** Without a service mesh or SPIFFE/SPIRE deployment, there is no cryptographic workload identity currently implemented (relies purely on basic Kubernetes ServiceAccounts).
  - **Authorization models:** *Determining what an authenticated entity is permitted to do.*
    - **Nexus Mapping:** Implemented natively via Kubernetes Role-Based Access Control (RBAC).
- **Gap analysis:** *Evaluating the difference between the current state of security and a desired future state.*
  - **Nexus Mapping:** Executed by comparing current cluster state against security baselines (e.g., using `kube-bench` for CIS benchmarks, or this exact SY0-701 mapping exercise).

### Zero Trust
- **Control Plane:** *The overarching system that evaluates context and decides whether to grant access.*
  - **Adaptive identity:** *Dynamically evaluating identity and risk context before granting access.*
    - **Nexus Mapping:** **[GAP IDENTIFIED]** Not natively implemented in the current baseline infrastructure.
  - **Threat scope reduction:** *Limiting the potential blast radius of an incident.*
    - **Nexus Mapping:** Achieved through strict Kubernetes namespace isolation and Kubernetes NetworkPolicies.
  - **Policy-driven access control:** *Access decisions based on centrally managed policies.*
    - **Nexus Mapping:** Enforced by Kyverno cluster admission policies.
  - **Policy Administrator:** *The entity or group responsible for creating and maintaining policy.*
    - **Nexus Mapping:** Git repository owners and maintainers (enforced via Pull Request approval workflows).
  - **Policy Engine:** *The component that evaluates the policy against the request.*
    - **Nexus Mapping:** Kyverno acts as the Kubernetes policy engine.
- **Data Plane:** *The actual systems, networks, and resources being protected.*
  - **Implicit trust zones:** *Areas within a network where all entities are inherently trusted.*
    - **Nexus Mapping:** Core Nexus seeks to eliminate these. However, pod-to-pod traffic within a single namespace without a service mesh enforcing strict mTLS acts as a localized implicit trust zone.
  - **Subject/System:** *The entity requesting access.*
    - **Nexus Mapping:** A Kubernetes Pod or associated Service Account.
  - **Policy Enforcement Point:** *The point where the access decision is executed (allowed or denied).*
    - **Nexus Mapping:** The Kubernetes API Server (via RBAC/Kyverno) and host-level enforcement (via Tetragon eBPF).

### Physical security
- **Bollards, Access control vestibule, Fencing, Video surveillance, Security guard, Access badge, Lighting, Sensors (Infrared, Pressure, Microwave, Ultrasonic):** *Controls designed to physically protect the facility, hardware, and personnel.*
  - **Nexus Mapping:** Inherited entirely from the physical deployment environment (e.g., data center controls, secure lab room). Core Nexus is a software stack and does not directly implement physical security.

### Deception and disruption technology
- *Technologies designed to mislead attackers, waste their resources, and detect early stage attacks (e.g., honeypots, honeyfiles).*
  - **Nexus Mapping:** **[GAP IDENTIFIED]** No native deception technologies or honeypots are currently deployed in the baseline infrastructure.


## 1.3 Explain the importance of change management processes and the impact to security

### Business processes impacting security operations
- **Approval process:** *The formal procedure for reviewing and approving changes before implementation.*
  - **Nexus Mapping:** Pull Request (PR) reviews and approvals in Git act as the formal approval gate.
- **Ownership:** *The individual or team accountable for a specific system, process, or data.*
  - **Nexus Mapping:** Repository owners (e.g., via CODEOWNERS files) dictate ownership of specific infrastructure components.
- **Stakeholders:** *Individuals or groups with an interest in the change or who may be affected by it.*
  - **Nexus Mapping:** Developers, SOC analysts, and platform engineers collaborating on Git issues and PRs.
- **Impact analysis:** *Evaluating the potential consequences of a change, including risks and resource requirements.*
  - **Nexus Mapping:** **[GAP IDENTIFIED]** Core Nexus relies on CI/CD checks (like `helm lint`), but does not have a formal business impact analysis tool or workflow integrated.
- **Test results:** *The outcomes of testing the change in a non-production environment.*
  - **Nexus Mapping:** Automated CI test suites and staging environment validations before merging to the `main` branch.
- **Backout plan:** *A predefined strategy to revert a change if it causes unexpected issues.*
  - **Nexus Mapping:** Argo CD provides automatic self-healing, and Git enables instant rollback (`git revert`) to a previous known-good state.
- **Maintenance window:** *A scheduled period during which authorized changes can be made with minimal impact on users.*
  - **Nexus Mapping:** **[GAP IDENTIFIED]** GitOps systems apply changes continuously. Formal maintenance windows require configuring Argo CD sync windows, which are currently not explicitly defined in the baseline.
- **Standard operating procedure:** *Documented step-by-step instructions for executing routine tasks.*
  - **Nexus Mapping:** Documented as Markdown playbooks in the `docs/` repository structure.

### Technical implications
- **Allow lists/deny lists:** *Explicitly permitting or blocking specific entities, actions, or content.*
  - **Nexus Mapping:** Defined via Kubernetes NetworkPolicies (allow/deny traffic) and Kyverno policies.
- **Restricted activities:** *Actions that are explicitly prohibited by policy or configuration.*
  - **Nexus Mapping:** Kyverno admission policies preventing privileged containers or root escalation.
- **Downtime:** *A period during which a system or service is unavailable.*
  - **Nexus Mapping:** Minimized via Kubernetes high availability (HA) deployments, rolling updates, and PodDisruptionBudgets.
- **Service restart / Application restart:** *Restarting a specific service or application.*
  - **Nexus Mapping:** Handled gracefully by Kubernetes Liveness/Readiness probes and ReplicaSet orchestrations.
- **Legacy applications:** *Older applications that may not support modern security controls.*
  - **Nexus Mapping:** Isolated within dedicated Kubernetes namespaces and restricted by strict NetworkPolicies.
- **Dependencies:** *Software, libraries, or external services that an application relies on.*
  - **Nexus Mapping:** Tracked via Software Bill of Materials (SBOMs) generated and evaluated against CVE databases.

### Documentation
- **Updating diagrams:** *Ensuring architectural diagrams reflect the current state of the environment.*
  - **Nexus Mapping:** Tracked as code in the `docs/architecture` directory (e.g., using Mermaid.js).
- **Updating policies/procedures:** *Ensuring written policies and procedures reflect changes in technology or processes.*
  - **Nexus Mapping:** Security policies are stored as code (Kyverno YAML manifests), ensuring they are inherently documented and versioned.

### Version control
- *The practice of tracking and managing changes to software code and configurations over time.*
  - **Nexus Mapping:** The fundamental backbone of Core Nexus. All infrastructure, applications, and policies are stored in a Git repository, ensuring traceability, rollback, and auditability (GitOps).

## 1.4 Explain the importance of using appropriate cryptographic solutions

### Public key infrastructure (PKI)
- **Public key:** *The publicly distributable key in an asymmetric pair used to encrypt data or verify a digital signature.*
  - **Nexus Mapping:** Used in Sigstore/Cosign verifications for container images and GPG signature verification for Git commits.
- **Private key:** *The secret key in an asymmetric pair used to decrypt data or create a digital signature.*
  - **Nexus Mapping:** Stored securely by developers or CI systems to sign container images and Git commits. Not stored in plain text.
- **Key escrow:** *A process where a trusted third party holds a copy of cryptographic keys.*
  - **Nexus Mapping:** **[GAP IDENTIFIED]** Core Nexus does not natively implement key escrow for workload keys, relying instead on HashiCorp Vault for secure dynamic key generation and lifecycle management.

### Encryption
- **Level:**
  - **Full-disk / Partition / Volume:** *Encrypting entire hardware drives or logical partitions.*
    - **Nexus Mapping:** Handled at the host OS level (e.g., LUKS) or cloud provider level (e.g., AWS EBS encryption), outside the direct scope of the Core Nexus Kubernetes payload.
  - **File:** *Encrypting individual files.*
    - **Nexus Mapping:** Used if encrypting GitOps secrets before committing (e.g., Mozilla SOPS).
  - **Database / Record:** *Encrypting data at rest within a database management system.*
    - **Nexus Mapping:** Implemented within specific stateful workloads (like Vault's internal storage or MinIO's server-side encryption).
- **Transport/communication:** *Securing data in transit across a network.*
  - **Nexus Mapping:** TLS for all external ingress and internal API communications.
- **Asymmetric:** *Using key pairs (public/private) for encryption/decryption or signing.*
  - **Nexus Mapping:** GPG commit signing, Cosign image signing.
- **Symmetric:** *Using a single shared key for both encryption and decryption.*
  - **Nexus Mapping:** AES encryption used for fast bulk data encryption at rest (e.g., MinIO object storage).
- **Key exchange:** *Securely transferring cryptographic keys between parties.*
  - **Nexus Mapping:** TLS handshakes (e.g., ECDHE) used during API and user traffic.
- **Algorithms / Key length:** *The mathematical rules and size of keys used for encryption.*
  - **Nexus Mapping:** Enforced via cluster-wide cryptographic policies (e.g., requiring AES-256 and modern ECC equivalents).

### Tools
- **Trusted Platform Module (TPM) / Hardware security module (HSM) / Secure enclave:** *Hardware-based security for cryptographic operations and key storage.*
  - **Nexus Mapping:** Provided by the underlying infrastructure (e.g., cloud KMS, physical HSMs). HashiCorp Vault can be configured to use these as its auto-unseal backend.
- **Key management system:** *A system for managing cryptographic keys and their lifecycles.*
  - **Nexus Mapping:** HashiCorp Vault serves as the primary KMS for the Core Nexus cluster.

### Obfuscation
- **Steganography / Tokenization / Data masking:** *Techniques to hide or obscure data.*
  - **Nexus Mapping:** Tokenization and masking are implemented at the application layer or via specific logging configurations (e.g., Vector masking PII before sending to Loki).

### Hashing / Salting / Key stretching
- *Techniques used to ensure data integrity and securely store passwords by converting data to fixed-length values and adding complexity.*
  - **Nexus Mapping:** Used by tools like HashiCorp Vault or application databases when securely storing user credentials. Image digests (SHA256) ensure container image integrity.

### Digital signatures
- *A mathematical scheme for verifying the authenticity of digital messages or documents.*
  - **Nexus Mapping:** Sigstore/Cosign for container images; GPG for Git commits.

### Blockchain / Public Ledger
- *A decentralized, distributed ledger that records the provenance of a digital asset.*
  - **Nexus Mapping:** Sigstore's Rekor provides an immutable, tamper-resistant transparency log (acting as a public ledger) for container image signatures.



### Certificates
- **Certificate authorities:** *Trusted entities that issue and manage digital certificates.*
  - **Nexus Mapping:** HashiCorp Vault acting as an internal Root/Intermediate CA, or `cert-manager` integrated with Let's Encrypt for external CAs.
- **Certificate revocation lists (CRLs) / Online Certificate Status Protocol (OCSP):** *Methods for checking if a certificate has been invalidated before its expiration date.*
  - **Nexus Mapping:** Handled by Kubernetes ingress controllers and client libraries when validating external connections.
- **Self-signed:** *Certificates signed by the same entity whose identity it certifies (not trusted by default).*
  - **Nexus Mapping:** Often used during initial local lab bootstrapping or within isolated test namespaces.
- **Third-party:** *Certificates issued by an external, globally trusted Certificate Authority.*
  - **Nexus Mapping:** Used for public-facing production ingresses (e.g., via Let's Encrypt).
- **Root of trust:** *A highly secure foundational component from which all other cryptographic trust is derived.*
  - **Nexus Mapping:** The Vault Root CA or underlying hardware TPMs/KMS used to unseal Vault.
- **Certificate signing request (CSR) generation:** *A formal request sent to a CA to apply for a digital certificate.*
  - **Nexus Mapping:** Automated heavily within the cluster using Kubernetes `cert-manager` Custom Resources (Certificate/Issuer).
- **Wildcard:** *A certificate that secures a domain and an unlimited number of its subdomains.*
  - **Nexus Mapping:** Utilized for core infrastructure domains (e.g., `*.core-nexus.local`) to simplify internal TLS management.
