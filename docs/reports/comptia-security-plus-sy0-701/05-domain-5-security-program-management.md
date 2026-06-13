# Domain 5.0: Security Program Management and Oversight

## 5.1 Summarize elements of effective security governance
- **Model Governance:** AI components within Core Nexus are treated as production artifacts. Governance mandates signed model artifacts, version pinning, dataset versioning, and explicitly forbids autonomous response without prior auditing controls.

## 5.2 Explain elements of the risk management process
- **Phased Implementation:** Core Nexus uses a phased roadmap (Phase 1 through Phase 3) to incrementally manage and reduce risk as the architecture matures from a Docker lab to a high-assurance Enterprise Platform.

## 5.3 Explain the processes associated with third-party risk assessment and management
- **Software Supply Chain Risk:** Core Nexus mitigates third-party supply chain risk by relying on secure factories that store SBOMs, attestation signing material, and vulnerability scan reports natively within MinIO.

## 5.4 Summarize elements of effective security compliance
- **Immutable Audit Trails:** Platform logs in Loki and security logs in Wazuh Indexer provide the necessary audit trails to prove compliance with security policies and organizational governance frameworks.

## 5.5 Explain types and purposes of audits and assessments
- *(To be refined: Mapping vulnerability assessments, policy audits, and architecture reviews).*

## 5.6 Given a scenario, implement security awareness practices
- *(To be refined: Focus on AI-driven SOC analyst workflows, playbooks, and Security+ labs as educational tools).*
