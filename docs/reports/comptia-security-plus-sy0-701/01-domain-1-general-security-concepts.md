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
  - **Nexus Mapping:** Wazuh agents detecting host-level anomalies and Falco detecting anomalous container behavior.
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

### Business processes impacting security operation
- **Approval process:** *(To be mapped)*
- **Ownership:** *(To be mapped)*
- **Stakeholders:** *(To be mapped)*
- **Impact analysis:** *(To be mapped)*
- **Test results:** *(To be mapped)*
- **Backout plan:** *(To be mapped)*
- **Maintenance window:** *(To be mapped)*
- **Standard operating procedure:** *(To be mapped)*

### Technical implications
- **Allow lists/deny lists:** *(To be mapped)*
- **Restricted activities:** *(To be mapped)*
- **Downtime:** *(To be mapped)*
- **Service restart:** *(To be mapped)*
- **Application restart:** *(To be mapped)*
- **Legacy applications:** *(To be mapped)*
- **Dependencies:** *(To be mapped)*

### Documentation
- **Updating diagrams:** *(To be mapped)*
- **Updating policies/procedures:** *(To be mapped)*

### Version control
- *(To be mapped)*

## 1.4 Explain the importance of using appropriate cryptographic solutions

### Public key infrastructure (PKI)
- **Public key:** *(To be mapped)*
- **Private key:** *(To be mapped)*
- **Key escrow:** *(To be mapped)*

### Encryption
- **Level:** *(To be mapped)*
  - **Full-disk:** *(To be mapped)*
  - **Partition:** *(To be mapped)*
  - **File:** *(To be mapped)*
  - **Volume:** *(To be mapped)*
  - **Database:** *(To be mapped)*
  - **Record:** *(To be mapped)*
- **Transport/communication:** *(To be mapped)*
- **Asymmetric:** *(To be mapped)*
- **Symmetric:** *(To be mapped)*
- **Key exchange:** *(To be mapped)*
- **Algorithms:** *(To be mapped)*
- **Key length:** *(To be mapped)*

### Tools
- **Trusted Platform Module (TPM):** *(To be mapped)*
- **Hardware security module (HSM):** *(To be mapped)*
- **Key management system:** *(To be mapped)*
- **Secure enclave:** *(To be mapped)*

### Obfuscation
- **Steganography:** *(To be mapped)*
- **Tokenization:** *(To be mapped)*
- **Data masking:** *(To be mapped)*

### Hashing
- *(To be mapped)*

### Salting
- *(To be mapped)*

### Digital signatures
- *(To be mapped)*

### Key stretching
- *(To be mapped)*

### Blockchain
- *(To be mapped)*

### Open public ledger
- *(To be mapped)*

### Certificates
- **Certificate authorities:** *(To be mapped)*
- **Certificate revocation lists (CRLs):** *(To be mapped)*
- **Online Certificate Status Protocol (OCSP):** *(To be mapped)*
- **Self-signed:** *(To be mapped)*
- **Third-party:** *(To be mapped)*
- **Root of trust:** *(To be mapped)*
- **Certificate signing request (CSR) generation:** *(To be mapped)*
- **Wildcard:** *(To be mapped)*
