# Domain 2.0: Threats, Vulnerabilities, and Mitigations

## 2.1 Compare and contrast common threat actors and motivations

### Threat actors
- **Nation-state:** *Highly skilled, well-funded government-backed attackers aiming for espionage, sabotage, or IP theft.*
  - **Nexus Mapping:** Core Nexus defends against this via air-gapping capabilities, strict supply chain validation (Sigstore/Cosign), and hardened container images (Chainguard).
- **Unskilled attacker:** *(Script kiddies) Individuals who use pre-written hacking tools without deep technical understanding.*
  - **Nexus Mapping:** Mitigated by baseline security hygiene, Kyverno admission controls, and non-root container enforcement.
- **Hacktivist:** *Attackers motivated by ideology, social issues, or political beliefs.*
  - **Nexus Mapping:** Defenses focus on preventing defacement or DoS via ingress rate limiting and strict RBAC.
- **Insider threat:** *Current/former employees or contractors who have legitimate access and abuse it intentionally or accidentally.*
  - **Nexus Mapping:** The primary threat to air-gapped systems. Mitigated by GitOps branch protections (requiring PR approvals), strict Kubernetes RBAC, and Vault audit logging.
- **Organized crime:** *Well-funded criminal groups focused on financial gain (e.g., ransomware, extortion).*
  - **Nexus Mapping:** Prevented via immutable infrastructure, read-only root filesystems, and continuous configuration synchronization (Argo CD self-healing).
- **Shadow IT:** *Employees using unauthorized IT systems or applications, inadvertently introducing risk without IT oversight.*
  - **Nexus Mapping:** Prevented centrally by Kyverno policies that restrict deployments exclusively to approved container registries (e.g., the local Zarf registry).

### Attributes of actors
- **Internal/external:** *Whether the actor originates inside the organization's perimeter or outside.*
  - **Nexus Mapping:** Internal threats are handled via RBAC and eBPF monitoring (Tetragon); external threats are handled via ingress controllers and NetworkPolicies.
- **Resources/funding:** *The level of financial and material backing the actor possesses.*
  - **Nexus Mapping:** Core Nexus assumes well-resourced adversaries, hence the use of cryptographic attestations and memory-safe tooling.
- **Level of sophistication/capability:** *The technical skill and advanced custom tooling available to the actor.*

### Motivations
- **Data exfiltration, Espionage, Service disruption, Blackmail, Financial gain, Philosophical/political beliefs, Ethical, Revenge, Disruption/chaos, War:** *The underlying reasons driving a threat actor to launch an attack.*
  - **Nexus Mapping:** While Core Nexus cannot control attacker motivations, it directly mitigates the *impacts* of these motivations (e.g., preventing Data Exfiltration via strict egress NetworkPolicies; preventing Service Disruption via Kubernetes High Availability and PodDisruptionBudgets).

## 2.2 Explain common threat vectors and attack surfaces

### Message-based
- **Email, SMS, IM:** *Vectors delivering phishing links or malware directly to users.*
  - **Nexus Mapping:** Core Nexus minimizes the impact of compromised endpoints via strict egress NetworkPolicies (preventing malware from phoning home) and host-level anomaly detection (Wazuh).

### Image-based
- *Malicious code hidden in image files (steganography) or compromised container images.*
  - **Nexus Mapping:** Nexus defends against compromised container images through rigorous scanning (Trivy/Grype), cryptographic signatures (Sigstore/Cosign), and Kyverno admission controls that block unsigned or vulnerable images.

### File-based
- *Malicious documents, scripts, or executables.*
  - **Nexus Mapping:** Mitigated by restricting execution environments to immutable containers with read-only root filesystems and monitoring abnormal file execution via eBPF (Tetragon).

### Voice call
- *Vishing (Voice Phishing) attacks targeting personnel.*
  - **Nexus Mapping:** Primarily a human vector. Outside the direct technical scope of the Core Nexus Kubernetes stack.

### Removable device
- *Malicious USB drives or external media.*
  - **Nexus Mapping:** Mitigated by the physical security of the data center/lab environment and host-level OS hardening.

### Vulnerable software
- **Client-based vs. agentless:** *Exploiting unpatched applications or underlying infrastructure components.*
  - **Nexus Mapping:** Mitigated through automated, declarative GitOps updates (Argo CD) and utilizing hardened, minimal container images (e.g., Chainguard) to drastically reduce the CVE surface area.

### Unsupported systems and applications
- *Legacy systems that no longer receive security patches.*
  - **Nexus Mapping:** If required, legacy workloads are aggressively isolated into dedicated Kubernetes namespaces and restricted by strict default-deny NetworkPolicies.

### Unsecure networks
- **Wireless, Wired, Bluetooth:** *Exploiting unencrypted or weakly secured network transit.*
  - **Nexus Mapping:** Mitigated by enforcing TLS on all ingress routes. **[GAP IDENTIFIED]** Internal pod-to-pod traffic lacks strict mTLS since a service mesh is not currently deployed.

### Open service ports
- *Unnecessary network ports left open, increasing the attack surface.*
  - **Nexus Mapping:** Mitigated by default-deny Kubernetes NetworkPolicies and strictly controlling `NodePort` or `LoadBalancer` exposure via Argo CD configuration review.

### Default credentials
- *Unchanged factory or default installation passwords.*
  - **Nexus Mapping:** Mitigated by injecting credentials dynamically via HashiCorp Vault, avoiding default passwords entirely in configuration files.

### Supply chain
- **Managed service providers (MSPs), Vendors, Suppliers:** *Compromises originating from upstream software providers or external partners.*
  - **Nexus Mapping:** A primary focus of Core Nexus. Defended against via the Zarf air-gapped packaging model, strict Software Bill of Materials (SBOM) validation, and Sigstore provenance tracking.

### Human vectors/social engineering
- **Phishing, Vishing, Smishing, Misinformation, Impersonation, BEC, Pretexting, Watering hole, Brand impersonation, Typosquatting:** *Psychological manipulation tricking users into making security mistakes.*
  - **Nexus Mapping:** While social engineering targets human behavior, Nexus limits the blast radius of a compromised user via strict Kubernetes Role-Based Access Control (RBAC) and least-privilege principles.

## 2.3 Explain various types of vulnerabilities

### Application
- **Memory injection / Buffer overflow:** *Exploiting memory management flaws to execute arbitrary code.*
  - **Nexus Mapping:** Mitigated by deploying memory-safe languages (Go/Rust) and using hardened, minimal container images (Chainguard) that lack the shell tooling needed for easy exploitation.
- **Race conditions (TOC/TOU):** *Exploiting the timing between checking a condition and using its result.*
  - **Nexus Mapping:** Handled by application-level secure coding practices.
- **Malicious update:** *Compromising the software update mechanism.*
  - **Nexus Mapping:** Core Nexus entirely prevents this via Sigstore/Cosign verification; Kyverno blocks any image update lacking a valid cryptographic signature.

### Operating system (OS)-based
- *Vulnerabilities inherent to the underlying host OS.*
  - **Nexus Mapping:** Mitigated by aggressive patching of Kubernetes nodes and ideally using immutable, container-optimized operating systems.

### Web-based
- **Structured Query Language injection (SQLi) / Cross-site scripting (XSS):** *Exploiting input validation flaws in web applications.*
  - **Nexus Mapping:** Addressed at the application layer. Ingress controllers can optionally be paired with Web Application Firewalls (WAF) to filter these payloads.

### Hardware
- **Firmware / End-of-life / Legacy:** *Vulnerabilities in physical devices or outdated, unsupported hardware.*
  - **Nexus Mapping:** Inherited from the physical deployment environment. Out of scope for the software payload.

### Virtualization
- **Virtual machine (VM) escape / Resource reuse:** *Breaking out of an isolated VM/container to interact with the host or other tenants.*
  - **Nexus Mapping:** A critical capability of Core Nexus. This is mitigated natively by the **gVisor** secure container runtime, which provides an application kernel sandbox preventing container-to-host escapes.

### Cloud-specific
- *Vulnerabilities arising from cloud misconfigurations (e.g., exposed storage buckets, overly permissive IAM).*
  - **Nexus Mapping:** Mitigated by infrastructure-as-code (Pulumi/Terraform) and CSPM (Cloud Security Posture Management) tools.

### Supply chain
- **Service provider / Hardware provider / Software provider:** *Vulnerabilities inherited from external vendors.*
  - **Nexus Mapping:** Handled via Zarf package definitions, strict SBOM generation, and vulnerability scanning in the CI/CD pipeline.

### Cryptographic
- *Using weak or deprecated cryptographic algorithms.*
  - **Nexus Mapping:** Mitigated by Kyverno and standard Ingress controller policies that enforce modern TLS (1.2/1.3) and strong ciphers.

### Misconfiguration
- *Improperly configuring systems, leading to unintended exposure.*
  - **Nexus Mapping:** GitOps (**Flux** image automation + **Argo CD** app delivery) enforces declarative configuration and corrects drift by syncing to Git (ADR 0003).

### Mobile device
- **Side loading / Jailbreaking:** *Installing unapproved apps or removing OS restrictions on mobile devices.*
  - **Nexus Mapping:** Out of scope for the Core Nexus infrastructure.

### Zero-day
- *A previously unknown vulnerability for which no patch currently exists.*
  - **Nexus Mapping:** Core Nexus aims to **contain unknown vulnerabilities** via defense-in-depth (e.g. sandboxing where deployed, read-only filesystems, runtime telemetry). This is **not** a claim of zero-day detection or prevention.

## 2.4 Given a scenario, analyze indicators of malicious activity

### Malware attacks
- **Ransomware, Trojan, Worm, Spyware, Bloatware, Virus, Keylogger, Logic bomb, Rootkit:** *Various forms of malicious software designed to disrupt, damage, or gain unauthorized access.*
  - **Nexus Mapping:** Mitigated heavily by immutable infrastructure. Read-only root filesystems prevent persistence (e.g., Ransomware/Rootkits). Strict egress NetworkPolicies prevent command-and-control (e.g., Spyware/Trojans). Tetragon (eBPF) detects unexpected binary executions.

### Physical attacks
- **Brute force, Radio frequency identification (RFID) cloning, Environmental:** *Attacks targeting the physical facilities or hardware.*
  - **Nexus Mapping:** Out of scope for the software payload. Handled by the physical facility hosting the underlying nodes.

### Network attacks
- **Distributed denial-of-service (DDoS) / DNS attacks / On-path / Credential replay:** *Attacks aimed at disrupting network availability or intercepting traffic.*
  - **Nexus Mapping:** Volumetric DDoS is mitigated by ingress rate limiting. On-path (MitM) and credential replay attacks are mitigated by enforcing strict TLS. Malicious network patterns are detected by Suricata.

### Application attacks
- **Injection, Buffer overflow, Replay, Privilege escalation, Forgery, Directory traversal:** *Exploiting flaws within application logic or memory.*
  - **Nexus Mapping:** Privilege escalation is explicitly blocked by Kyverno policies (disallowing `privileged: true`). Buffer overflows are contained by the gVisor sandbox. Web-based attacks are mitigated by WAF configurations at the ingress tier.

### Cryptographic attacks
- **Downgrade, Collision, Birthday:** *Exploiting weaknesses in cryptographic algorithms or implementations.*
  - **Nexus Mapping:** Prevented by ingress and cluster policies enforcing modern cipher suites and disabling legacy protocol versions (e.g., forcing TLS 1.2+).

### Password attacks
- **Spraying, Brute force:** *Attempting to guess passwords.*
  - **Nexus Mapping:** Mitigated by relying on cryptographic tokens (Vault) or external identity providers instead of static passwords, and monitoring authentication anomalies via Wazuh.

### Indicators
- **Account lockout, Concurrent session usage, Blocked content, Impossible travel, Resource consumption, Resource inaccessibility, Out-of-cycle logging, Published/documented, Missing logs:** *Signs that an attack is occurring or has occurred.*
  - **Nexus Mapping:** Indicators are aggregated centrally. Resource consumption spikes (e.g., crypto-mining) are detected by Prometheus/Grafana. Suspicious host activity or log tampering (Missing logs) is flagged by Wazuh and Vector/Loki.

## 2.5 Explain the purpose of mitigation techniques used to secure the enterprise

### Segmentation
- *Dividing a network into smaller, isolated sub-networks to contain breaches.*
  - **Nexus Mapping:** Implemented via Kubernetes namespaces and enforced tightly by default-deny NetworkPolicies.

### Access control
- **Access control list (ACL) / Permissions:** *Rules that grant or deny access to resources.*
  - **Nexus Mapping:** Implemented natively via Kubernetes Role-Based Access Control (RBAC), mapping users/groups to specific Roles or ClusterRoles.

### Application allow list
- *Explicitly permitting only approved software to execute.*
  - **Nexus Mapping:** Kyverno admission controllers act as a cluster-wide allow list, blocking any pod that uses an unapproved or unsigned container image.

### Isolation
- *Separating processes or systems so they cannot interact maliciously.*
  - **Nexus Mapping:** Achieved through Kubernetes namespaces and significantly enhanced by the **gVisor** secure container runtime sandbox.

### Patching
- *Applying updates to software to fix vulnerabilities.*
  - **Nexus Mapping:** Executed declaratively via GitOps; changing the image tag in Git automatically rolls out the patched container via Argo CD.

### Encryption
- *Converting data into a secure format to prevent unauthorized access.*
  - **Nexus Mapping:** Vault manages encryption for data at rest (via Transit secrets or encrypted storage). TLS manages encryption for data in transit.

### Monitoring
- *Continuously observing systems for anomalies or policy violations.*
  - **Nexus Mapping:** Handled by a robust observability stack: Prometheus (metrics), Loki (logs), Tetragon (eBPF runtime events), and Suricata (network events).

### Least privilege
- *Granting users and systems only the minimum access necessary to perform their functions.*
  - **Nexus Mapping:** A core tenet. Containers are forced to run as non-root (via Kyverno) and service accounts are given strictly scoped RBAC permissions.

### Configuration enforcement
- *Ensuring systems remain in their desired, secure state.*
  - **Nexus Mapping:** Argo CD provides continuous configuration enforcement by detecting drift and automatically syncing the cluster state back to the Git source of truth.

### Decommissioning
- *Securely retiring systems or data when no longer needed.*
  - **Nexus Mapping:** Deleting an Argo CD Application resource cleanly and completely tears down all associated Kubernetes manifests and workloads.

### Hardening techniques
- **Encryption, Endpoint protection, Host-based firewall, HIPS, Disabling ports, Default password changes, Removal of unnecessary software:** *Various methods to reduce the attack surface.*
  - **Nexus Mapping:** Handled holistically by deploying minimal, distroless container images (Chainguard) which inherently lack package managers and unnecessary software. Host protection is provided by Tetragon and Wazuh. Default passwords are removed entirely in favor of dynamically injected Vault secrets.
