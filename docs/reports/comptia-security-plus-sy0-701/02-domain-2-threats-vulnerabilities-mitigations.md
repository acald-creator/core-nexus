# Domain 2.0: Threats, Vulnerabilities, and Mitigations

## 2.1 Compare and contrast various types of threat actors and motivations
- **Controlled Adversary Emulation:** The Athena fuzzer (`nexus-athena`) simulates various threat actor behaviors to generate realistic malicious telemetry for training the AI inference engine.

## 2.2 Explain common threat vectors and attack surfaces
- **Red Team Fuzzing:** The `nexus-athena` container serves as an isolated traffic and attack generator. It demonstrates common attack surfaces and enables controlled security testing without compromising host environments.

## 2.3 Given a scenario, analyze indicators of malicious activity
- **Telemetry Analysis:** Wazuh and the AI-SOC Inference Engine continuously analyze system logs and network flows to identify malware signatures, password spraying, and lateral movement.

## 2.4 Explain the purpose of mitigation techniques used to secure the enterprise
- **Hybrid Sensor (Network & Host):** 
  - **Suricata:** Identifies known protocol anomalies and malicious packet signatures, outputting network indicators via `eve.json`.
  - **Runtime Telemetry (Falco/Wazuh agents):** Captures host-level indicators such as unauthorized process execution or abnormal system calls, augmenting network-only visibility.
- **AI Triage:** Transforms indicators of malicious activity into behavioral features (tensors) that detect anomalies not caught by static signatures.
