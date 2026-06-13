# Domain 3.0: Security Architecture

## 3.1 Compare and contrast security implications of different architecture models
- **Progressive Architecture Deployment:** Core Nexus provides a roadmap transitioning from a fast local Docker lab to a Kubernetes Production Model with GitOps (Argo CD), and optionally to an air-gapped delivery model (UDS/Zarf).
- **Separation of Duties:** The Platform UI acts as a unified launchpad, but SOC findings are explicitly routed to purpose-built SOC clients (e.g., Wazuh Dashboard), enforcing separation between platform operations and security investigations.

## 3.2 Given a scenario, apply security principles to secure enterprise infrastructure
- **Secrets Management:** Migration from insecure `.env` files and hardcoded secrets to a robust secrets architecture. Vault HA (via Helm) is designated as the production secrets manager, decoupling secrets from the UDS baseline.

## 3.3 Compare and contrast concepts and strategies to protect data
- **Data Immutability:** S3-compatible MinIO clusters provide storage for immutable evidence logs and secure system backups.

## 3.4 Explain the importance of resilience and recovery in security architecture
- **Infrastructure as Code (IaC) & GitOps:** Argo CD and Pulumi ensure rapid recovery of the Nexus environment from known-good, version-controlled configurations.
- **Backup & Recovery:** Velero (in the UDS baseline) is designated for full cluster backup and disaster recovery.
