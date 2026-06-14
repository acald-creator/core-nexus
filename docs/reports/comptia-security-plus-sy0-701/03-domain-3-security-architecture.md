# Domain 3.0: Security Architecture

## 3.1 Compare and contrast security implications of different architecture models

### Architecture and infrastructure concepts
- **Cloud / Responsibility matrix / Hybrid considerations / Third-party vendors:** *Using remote servers hosted on the internet.*
  - **Nexus Mapping:** Core Nexus is cloud-agnostic but generally deployed as Infrastructure as a Service (IaaS). Under the shared responsibility model, the cloud provider secures the physical hardware, while Core Nexus secures the Kubernetes platform, data, and applications.
- **Infrastructure as code (IaC):** *Managing and provisioning infrastructure through machine-readable definition files.*
  - **Nexus Mapping:** A foundational pillar. Infrastructure is provisioned via Pulumi/Terraform, and cluster state is managed declaratively via GitOps (Argo CD).
- **Serverless:** *A cloud computing execution model where the provider dynamically manages the allocation of machine resources.*
  - **Nexus Mapping:** Not utilized. Core Nexus explicitly uses containerized workloads running on a dedicated Kubernetes cluster.
- **Microservices:** *An architectural style that structures an application as a collection of loosely coupled services.*
  - **Nexus Mapping:** Fully embraced. The system divides operations into discrete components (SOC, Athena, Workbench, AI triage) running as separate Pods.
- **Network infrastructure / Software-defined networking (SDN):** *Virtualizing the network control plane.*
  - **Nexus Mapping:** Handled natively by the Kubernetes Container Network Interface (CNI), providing software-defined routing and network policies.
- **Physical isolation / Air-gapped / Logical segmentation:** *Separating networks to prevent unauthorized communication.*
  - **Nexus Mapping:** Core Nexus excels at **air-gapped** deployments using Zarf packages (which bundle all dependencies). Inside the cluster, **logical segmentation** is enforced via Kubernetes namespaces and NetworkPolicies.
- **On-premises:** *Software and technology located within the physical confines of an enterprise.*
  - **Nexus Mapping:** A primary deployment target for Core Nexus, providing full sovereignty over data and hardware.
- **Centralized vs. decentralized:** *Where control and data are located.*
  - **Nexus Mapping:** Decentralized execution (distributed Pods) with centralized management and configuration (GitOps/Argo CD).
- **Containerization:** *Packaging software code with just the OS libraries and dependencies required to run the code.*
  - **Nexus Mapping:** The fundamental building block of Core Nexus payloads (Docker/containerd/CRI-O).
- **Virtualization:** *Creating a virtual version of a resource, such as a server or OS.*
  - **Nexus Mapping:** Host nodes are typically VMs; container workloads are further isolated using **gVisor** for secure kernel virtualization/sandboxing.
- **IoT / ICS/SCADA / RTOS / Embedded systems:** *Specialized, often constrained computing devices.*
  - **Nexus Mapping:** Out of scope for the Core Nexus infrastructure itself, though Core Nexus components (like Wazuh/Suricata) may monitor networks containing these devices.
- **High availability:** *Systems that are durable and likely to operate continuously without failure.*
  - **Nexus Mapping:** Inherited through Kubernetes HA control planes, multi-node worker pools, and workload ReplicaSets.

### Considerations
- **Availability, Resilience, Cost, Responsiveness, Scalability, Ease of deployment, Risk transference, Ease of recovery, Patch availability, Inability to patch, Power, Compute:** *Various factors influencing architectural design decisions.*
  - **Nexus Mapping:** Core Nexus specifically optimizes for **Ease of deployment** (via Zarf air-gap packages), **Scalability/Resilience** (via Kubernetes orchestration), and **Ease of recovery** (via GitOps, enabling cluster rebuilds from scratch using the Git source of truth).

## 3.2 Given a scenario, apply security principles to secure enterprise infrastructure

### Infrastructure considerations
- **Device placement / Security zones / Attack surface / Connectivity:** *Designing the layout of the network to minimize risk.*
  - **Nexus Mapping:** Core Nexus minimizes the attack surface by defaulting to a private cluster topology. Workloads are strictly placed in isolated Kubernetes namespaces (security zones) with default-deny connectivity.
- **Failure modes (Fail-open / Fail-closed):** *How a system behaves when a component fails.*
  - **Nexus Mapping:** Security controls (like Kyverno admission policies and NetworkPolicies) are explicitly designed to **fail-closed**, ensuring that if the policy engine goes down, no new unsanctioned workloads can be deployed.
- **Device attribute (Active vs. passive / Inline vs. tap/monitor):** *How a security tool interacts with traffic.*
  - **Nexus Mapping:** Core Nexus utilizes both. Suricata generally acts as a passive tap/monitor for network flows, while Tetragon (eBPF) provides active, inline enforcement at the kernel level.
- **Network appliances (Jump server, Proxy server, IPS/IDS, Load balancer, Sensors):** *Hardware or virtual devices performing network functions.*
  - **Nexus Mapping:** The cluster exposes services via a Load Balancer to the Ingress controller. Suricata acts as the IDS/Sensor. Jump servers (bastions) may be used at the infrastructure level to access the Kube API securely.
- **Port security (802.1X / Extensible Authentication Protocol (EAP)):** *Securing physical network switch ports.*
  - **Nexus Mapping:** Inherited from the physical data center or cloud provider; out of scope for the Kubernetes payload.
- **Firewall types (WAF, UTM, NGFW, Layer 4/Layer 7):** *Different methods of filtering network traffic.*
  - **Nexus Mapping:** Core Nexus enforces Layer 4 filtering via Kubernetes NetworkPolicies and Layer 7 filtering via Ingress controllers (which can be augmented with Web Application Firewalls).

### Secure communication/access
- **Virtual private network (VPN) / Remote access / Tunneling (TLS / IPSec) / SD-WAN / SASE:** *Methods for securing traffic crossing untrusted networks.*
  - **Nexus Mapping:** **TLS** is strictly enforced for all ingress traffic reaching the cluster. Access to the underlying nodes or the Kube API typically requires an infrastructure-level VPN or SD-WAN/SASE client (e.g., Tailscale or corporate VPN), which wraps the connection in IPSec or WireGuard.

### Selection of effective controls
- *Choosing the right security measure for the specific risk.*
  - **Nexus Mapping:** Core Nexus relies heavily on **defense-in-depth**. It layers declarative GitOps (Argo CD), memory-safe minimal images (Chainguard), runtime eBPF enforcement (Tetragon), and host-level SIEM (Wazuh) to provide overlapping, effective controls.

## 3.3 Compare and contrast concepts and strategies to protect data

### Data types
- **Regulated, Trade secret, Intellectual property, Legal information, Financial information:** *Different categories of data based on its content and usage.*
  - **Nexus Mapping:** Core Nexus is designed to handle highly sensitive data agnostically. It treats all internal payloads as critical, relying on the platform's overarching security controls (e.g., air-gapping, encryption) to protect whatever data type is processed.
- **Human and non-human-readable:** *Data formatted for people vs. machines.*
  - **Nexus Mapping:** Non-human-readable configurations and secrets are managed via HashiCorp Vault and GitOps pipelines.

### Data classifications
- **Sensitive, Confidential, Public, Restricted, Private, Critical:** *Organizational labels applied to data to determine its required level of protection.*
  - **Nexus Mapping:** Core Nexus supports strict data classification by physically isolating "Critical" data into separate air-gapped clusters, or logically isolating "Confidential" vs. "Public" data into separate Kubernetes namespaces with strict NetworkPolicies.

### General data considerations
- **Data states:**
  - **Data at rest:** *Data stored on persistent media.*
    - **Nexus Mapping:** Encrypted via host-level volume encryption (e.g., AWS EBS encryption or LUKS) and HashiCorp Vault.
  - **Data in transit:** *Data moving across a network.*
    - **Nexus Mapping:** Protected via strict TLS 1.2+ enforcement for all cluster ingress and API traffic.
  - **Data in use:** *Data actively being processed in memory.*
    - **Nexus Mapping:** Protected by isolating the application kernel using **gVisor**, preventing unauthorized memory access across container boundaries.
- **Data sovereignty:** *Ensuring data is subject to the laws and governance structures of the nation where it is physically located.*
  - **Nexus Mapping:** Core Nexus inherently supports data sovereignty because it can be deployed fully on-premises without "phoning home" to a centralized vendor SaaS.
- **Geolocation:** *Identifying the geographic location of an entity.*
  - **Nexus Mapping:** Can be utilized by an external Web Application Firewall (WAF) to apply geo-blocking before traffic reaches the Kubernetes ingress.

### Methods to secure data
- **Geographic restrictions / Segmentation / Permission restrictions:** *Controlling access based on location, network boundaries, and user rights.*
  - **Nexus Mapping:** Executed via WAF rules, Kubernetes NetworkPolicies (Segmentation), and strict Kubernetes Role-Based Access Control (Permissions).
- **Encryption / Hashing / Masking / Tokenization / Obfuscation:** *Transforming data to protect its confidentiality and integrity.*
  - **Nexus Mapping:** Encryption and Hashing are handled by Vault and TLS. Masking/Tokenization are typically application-layer responsibilities, though logging agents (like Vector) can be configured to mask PII before logs reach Loki.

## 3.4 Explain the importance of resilience and recovery in security architecture

### High availability
- **Load balancing vs. clustering:** *Distributing workloads across multiple resources to prevent single points of failure.*
  - **Nexus Mapping:** Core Nexus uses both. It deploys a **clustered** Kubernetes environment (multi-node K3s/RKE2) and uses **LoadBalancers** at the ingress layer to distribute incoming traffic across the cluster.

### Site considerations
- **Hot, Cold, Warm, Geographic dispersion:** *Strategies for alternate processing sites in the event of a disaster.*
  - **Nexus Mapping:** Determined by the physical infrastructure provider. Core Nexus can be easily restored to a Cold or Warm site by reapplying the Zarf packages and Argo CD Git repository.

### Platform diversity / Multi-cloud systems
- *Using multiple computing platforms or cloud providers to reduce vendor lock-in and systemic risk.*
  - **Nexus Mapping:** A core benefit of Kubernetes and Zarf. Core Nexus is entirely cloud-agnostic and can run identically on AWS, Azure, GCP, or bare-metal air-gapped servers.

### Continuity of operations
- *Ensuring essential functions continue during and after a disaster.*
  - **Nexus Mapping:** Because Core Nexus is entirely defined as code (GitOps), an entire destroyed cluster can be stood back up rapidly by deploying Kubernetes and pointing Argo CD at the repository.

### Capacity planning
- **People, Technology, Infrastructure:** *Determining the resources needed to meet future demands.*
  - **Nexus Mapping:** Technology and infrastructure capacity are managed via Kubernetes Cluster Autoscalers (if in the cloud) or by carefully provisioning physical worker nodes.

### Testing
- **Tabletop exercises, Fail over, Simulation, Parallel processing:** *Validating disaster recovery and incident response plans.*
  - **Nexus Mapping:** The `nexus-workbench` can be explicitly utilized during tabletop exercises to simulate attacks, test incident response runbooks, or run AI triage models against mock data.

### Backups
- **Onsite/offsite, Frequency, Encryption, Snapshots, Recovery, Replication, Journaling:** *Strategies for duplicating and storing data securely for recovery.*
  - **Nexus Mapping:** Handled natively by **Velero**, which is deployed in Core Nexus to take scheduled, encrypted snapshots of Kubernetes resources and persistent volumes, storing them in an S3-compatible backend (like MinIO).

### Power
- **Generators, Uninterruptible power supply (UPS):** *Ensuring continuous electricity.*
  - **Nexus Mapping:** Inherited from the physical data center or server closet hosting the nodes. Out of scope for the software payload.
