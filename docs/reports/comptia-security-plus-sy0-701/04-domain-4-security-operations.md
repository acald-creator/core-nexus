# Domain 4.0: Security Operations

## 4.1 Given a scenario, apply common security techniques to computing resources
- **Workload Hardening:** Core Nexus prefers hardened Chainguard images and nonroot (UID 65532) executions to apply robust security techniques directly to the computing resources.

## 4.2 Explain the security implications of proper hardware, software, and data asset management
- *(To be refined: Mapping SBOMs, software factory dependencies, and hardware lifecycle).*

## 4.3 Explain various activities associated with vulnerability management
- **Continuous Monitoring:** Wazuh agents continuously monitor workloads for missing patches, while Falco acts as the runtime security engine alerting on abnormal container behaviors.

## 4.4 Explain security alerting and monitoring concepts and tools
- **SIEM / Event Store:** Wazuh operates as the near-term SOC event store. Telemetry starts in Wazuh rather than generalized platform logging.
- **AI-SOC Inference Engine:** Ingests Wazuh and Suricata events, applies mathematical enrichment, and outputs structured triage JSON with a calculated threat score to reduce alert fatigue.

## 4.5 Modify enterprise capabilities to enhance security
- *(To be refined: Mapping platform updates, Istio configurations, and security capability upgrades).*

## 4.6 Given a scenario, implement and maintain identity and access management
- **SSO and Identity:** The UDS Core Baseline implements Keycloak for identity management and authentication across mission applications.

## 4.7 Explain the importance of automation and orchestration related to secure operations
- **GitOps Reconciliation:** Argo CD automatically orchestrates secure configuration deployment, preventing configuration drift from the approved Git source of truth.

## 4.8 Explain appropriate incident response activities
- **Evidence Gathering & Containment:** The `nexus-workbench` (JupyterLab) provides analysts with centralized runbooks and tooling to contain threats and capture evidence from lab networks.

## 4.9 Given a scenario, use data sources to support an investigation
- **Log Correlation:** Incident investigations rely on correlating `eve.json` from Suricata (network data source) with process telemetry from Wazuh agents (host data source), along with AI triage labels.
