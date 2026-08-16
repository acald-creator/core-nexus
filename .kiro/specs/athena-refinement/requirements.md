# Requirements Document

## Introduction

This feature refines the Athena adversary emulation subsystem of Underground Nexus through two coordinated efforts: modernizing the `nexus-athena` Docker image into a multi-stage, multi-platform build with tiered runtime profiles, and creating a new `athena-agents` repository housing an AI offensive agent framework for autonomous security testing within a purple-team feedback loop. The goal is to make Athena faster to build, safer by default, and capable of generating labeled attack telemetry that feeds directly into the AI-SOC inference pipeline for closed-loop detection evaluation.

## Glossary

- **Athena_Image**: The `nexus-athena` Docker container image built from a Kali Linux base, providing red-team and security testing tooling.
- **Athena_Core_Target**: A lightweight multi-stage Docker build target containing recon and scripting tools (Nmap, Python, networking utilities) without heavy exploitation frameworks.
- **Athena_Full_Target**: A complete multi-stage Docker build target extending Athena_Core_Target with Metasploit Framework, Wireshark, and radare2.
- **Athena_Agent**: An AI-driven autonomous offensive testing agent that follows an observe/plan/act/reflect loop to execute security test scenarios against approved lab targets.
- **Agent_Orchestrator**: The Python-based orchestration layer managing Athena_Agent lifecycle, tool dispatch, memory, and LLM inference backends.
- **Rust_Primitives**: High-performance offensive tool binaries written in Rust (port scanner, protocol fuzzer, packet crafter) invoked by the Agent_Orchestrator.
- **Purple_Team_Loop**: A closed feedback cycle where Athena generates offensive traffic, SOC sensors detect it, the AI_Inference_Engine triages it, and the Eval_Harness measures detection accuracy.
- **AI_Inference_Engine**: The existing AI-SOC inference service (Component B) that scores and labels security events from Wazuh and Suricata.
- **Eval_Harness**: A component that reconciles Athena ground-truth labels against AI_Inference_Engine predictions to compute precision, recall, and F1 metrics.
- **Ground_Truth_Schema**: A structured data format for labeled attack telemetry produced by Athena_Agent, including scenario identity, technique classification, and expected outcomes.
- **Runtime_Profile**: A named set of Linux capabilities, security contexts, and network policies defining the privilege level of an Athena deployment.
- **NetworkPolicy**: A Kubernetes resource restricting network traffic to and from Athena pods, enforcing lab isolation.
- **Exploit_Lab_Profile**: A Runtime_Profile granting elevated privileges for Metasploit and attack simulation labs, requiring explicit opt-in.
- **Packet_Lab_Profile**: A Runtime_Profile granting NET_ADMIN and NET_RAW capabilities for Wireshark and packet capture labs.
- **SOC_Pipeline**: The detection and event processing chain consisting of Suricata sensors, Wazuh agents/manager, and the AI_Inference_Engine.
- **LLM_Backend**: An inference server providing language model capabilities to Athena_Agent (Ollama, vLLM, or llama.cpp).
- **Tool_Registry**: A configuration-driven catalog of offensive tools available to Athena_Agent, mapping tool names to invocation commands and capability requirements.

## Requirements

### Requirement 1: Multi-Stage Docker Build with Tiered Targets

**User Story:** As a platform engineer, I want the Athena Docker image to use a multi-stage, multi-platform build with separate lightweight and full targets, so that I can reduce build times and image size for labs that only need recon tools.

#### Acceptance Criteria

1. THE Athena_Image build definition SHALL produce two named build targets: `athena-core` and `athena-full`.
2. WHEN the `athena-core` target is built, THE Athena_Image SHALL include Nmap, Python 3, Scapy, git, curl, wget, netcat, iproute2, dnsutils, and tcpdump without Metasploit Framework, Wireshark, or radare2.
3. WHEN the `athena-full` target is built, THE Athena_Image SHALL extend the `athena-core` target and additionally include Metasploit Framework, Wireshark, and radare2.
4. THE Athena_Image build definition SHALL support both `linux/amd64` and `linux/arm64` platforms from a single Dockerfile.
5. THE Athena_Image build definition SHALL NOT declare VOLUME directives for `/var/run` or `/var/lib/docker/volumes`.
6. WHEN radare2 is included in the `athena-full` target, THE Athena_Image SHALL pin the radare2 build to a specific tagged release rather than tracking a branch tip.
7. THE `athena-core` target compressed image size SHALL NOT exceed 1.5 GB.
8. THE Athena_Image SHALL include a non-root user (UID 1000) as the default execution identity, and the Dockerfile SHALL document the required Runtime_Profile capabilities as comments or labels.

### Requirement 2: Exploit-Lab Runtime Profile Implementation

**User Story:** As a security lab operator, I want a fully implemented exploit-lab runtime profile for Docker Compose and Kubernetes, so that I can run Metasploit attack simulations with explicit elevated privileges in an isolated environment.

#### Acceptance Criteria

1. THE Exploit_Lab_Profile SHALL be defined in the Docker Compose profiles file with explicit `cap_add` entries for NET_ADMIN, NET_RAW, and SYS_PTRACE, and SHALL attach to the `athena_lab` network only.
2. THE Exploit_Lab_Profile SHALL be defined as a Kubernetes Deployment manifest at `deploy/kubernetes/base/athena-exploit-lab.yaml`.
3. WHEN the Exploit_Lab_Profile is activated in Docker Compose, THE Athena container SHALL run with `no-new-privileges` security option enabled and all capabilities dropped before the explicit `cap_add` entries are applied.
4. THE Exploit_Lab_Profile Kubernetes manifest SHALL set `replicas: 0` by default, requiring explicit `kubectl scale` to activate.
5. THE Exploit_Lab_Profile Kubernetes manifest SHALL document required Linux capabilities (NET_ADMIN, NET_RAW, SYS_PTRACE) as annotations on the Deployment resource.
6. WHEN the Exploit_Lab_Profile is activated via Docker Compose, THE profile SHALL be gated behind a named Compose profile requiring `--profile exploit-lab` to start.

### Requirement 3: Kubernetes NetworkPolicy for Athena Isolation

**User Story:** As a cluster administrator, I want Kubernetes NetworkPolicies applied to the Athena namespace, so that Athena pods cannot reach production services or SOC control-plane components by default.

#### Acceptance Criteria

1. THE NetworkPolicy SHALL deny all ingress traffic to pods in the `nexus-athena` namespace when no profile-specific policy explicitly permits it.
2. THE NetworkPolicy SHALL deny all egress traffic from pods in the `nexus-athena` namespace except DNS resolution (UDP port 53) to the cluster DNS service (kube-dns/CoreDNS in the `kube-system` namespace) when no profile-specific policy explicitly permits additional egress.
3. WHERE the Packet_Lab_Profile is active, THE NetworkPolicy SHALL allow egress from pods in the `nexus-athena` namespace only to pods carrying the label `nexus-lab-target: "true"` in namespaces carrying the label `nexus-lab-network: "true"`.
4. WHERE the Exploit_Lab_Profile is active, THE NetworkPolicy SHALL allow egress from pods in the `nexus-athena` namespace only to pods carrying the label `nexus-lab-target: "true"` in namespaces carrying the label `nexus-lab-network: "true"`.
5. THE NetworkPolicy SHALL deny egress from the `nexus-athena` namespace to any namespace carrying the label `nexus-zone: "soc"` (hosting Wazuh manager, Wazuh indexer, and Wazuh dashboard), regardless of which profile is active.
6. IF a pod in `nexus-athena` attempts to communicate with a non-allowed destination, THEN THE NetworkPolicy SHALL drop the connection attempt and existing allowed connections from other pods in the namespace SHALL continue uninterrupted.
7. WHEN a profile-specific NetworkPolicy is removed from the `nexus-athena` namespace, THE default-deny policy SHALL revert egress permissions to DNS-only within 30 seconds of the policy object deletion.

### Requirement 4: Agent Orchestrator with Observe/Plan/Act/Reflect Loop

**User Story:** As a security researcher, I want an AI agent orchestrator that executes an observe/plan/act/reflect loop against approved lab targets, so that I can generate diverse offensive scenarios without manual command entry.

#### Acceptance Criteria

1. THE Agent_Orchestrator SHALL implement a four-phase execution cycle where: observe produces a structured target-state snapshot passed to plan, plan selects a technique and tool from the Tool_Registry and outputs an action specification, act executes the action specification and returns a result record, and reflect evaluates the result record against the action specification and appends a summary to the action history.
2. WHEN the Agent_Orchestrator starts a scenario, THE Agent_Orchestrator SHALL validate that the target is present in an approved target allowlist before executing any action.
3. IF the Agent_Orchestrator receives a target not in the allowlist, THEN THE Agent_Orchestrator SHALL refuse execution and log the rejected target.
4. THE Agent_Orchestrator SHALL support configurable LLM_Backend selection among Ollama, vLLM, and llama.cpp inference servers.
5. WHEN the Agent_Orchestrator completes the act phase, THE Agent_Orchestrator SHALL emit a Ground_Truth_Schema record with scenario_id, run_id, timestamp, target, technique, payload_family, expected_result, and label fields.
6. WHEN the Agent_Orchestrator reaches the configured maximum number of actions per scenario (minimum configurable value of 1, maximum configurable value of 1000), THE Agent_Orchestrator SHALL halt the execution cycle, emit a final Ground_Truth_Schema record summarizing the scenario outcome, and log the termination reason as limit-reached.
7. WHILE the Agent_Orchestrator is executing a scenario, THE Agent_Orchestrator SHALL maintain an in-memory action history accessible to the reflect phase.
8. IF any phase of the execution cycle fails due to target unreachability, tool execution error, or LLM_Backend timeout, THEN THE Agent_Orchestrator SHALL halt the scenario, log the failure phase and error details to the audit trail, and emit a Ground_Truth_Schema record with the label field set to `needs_review`.

### Requirement 5: Rust Offensive Primitives

**User Story:** As an offensive tool developer, I want high-performance Rust binaries for port scanning, protocol fuzzing, and packet crafting, so that the agent can execute low-latency operations that Python cannot efficiently perform.

#### Acceptance Criteria

1. THE Rust_Primitives SHALL include an asynchronous TCP port scanner that accepts a target address and port range (specified as two integers representing the start port and end port within 1–65535 inclusive) as CLI arguments, and outputs results as JSON to stdout containing at minimum the fields: target address, each scanned port number, and its status (open or closed).
2. THE Rust_Primitives SHALL include a protocol fuzzer that accepts a target address, protocol type, seed (unsigned 64-bit integer), and an iteration count (minimum 1, maximum 1000000, default 1000) as CLI arguments, and outputs mutation results as JSON to stdout containing at minimum the fields: seed, iteration index, mutated payload size in bytes, and protocol type.
3. THE Rust_Primitives SHALL include a packet crafter that accepts protocol parameters as CLI arguments and outputs crafted packet metadata as JSON to stdout containing at minimum the fields: protocol, total packet length in bytes, and a hex-encoded payload representation.
4. IF input validation fails when a Rust_Primitives binary is invoked, THEN THE Rust_Primitives binary SHALL exit with a non-zero exit code and write a JSON object to stderr containing at minimum the fields: error category and a human-readable message indicating the validation failure.
5. THE Rust_Primitives SHALL compile to statically-linked binaries for `x86_64-unknown-linux-musl` and `aarch64-unknown-linux-musl` targets.
6. THE Rust_Primitives port scanner SHALL accept a concurrency limit as a CLI argument (minimum 1, maximum 65535, default 1024) controlling the maximum number of simultaneous outstanding TCP connection attempts.
7. THE Rust_Primitives port scanner SHALL accept a per-connection timeout as a CLI argument (minimum 100 milliseconds, maximum 30000 milliseconds, default 3000 milliseconds) after which an unanswered connection attempt is classified as closed.
8. WHEN the Rust_Primitives protocol fuzzer completes the configured number of iterations or encounters a connection failure, THE Rust_Primitives protocol fuzzer SHALL terminate and write a summary JSON object to stdout containing total iterations completed and elapsed duration in milliseconds.

### Requirement 6: Tool Registry

**User Story:** As a platform engineer, I want a configuration-driven tool registry mapping tool names to invocation commands, so that the agent can discover and invoke offensive tools without hard-coded paths.

#### Acceptance Criteria

1. THE Tool_Registry SHALL be defined as a structured configuration file (TOML or YAML) where each tool entry maps a unique tool identifier to an executable path, an invocation type field indicating subprocess or in-process invocation, an argument schema declaring accepted parameter names and types, and a list of required Runtime_Profile capabilities.
2. WHEN the Agent_Orchestrator starts, THE Agent_Orchestrator SHALL load and parse the Tool_Registry file and reject startup with a descriptive error if the file is missing, unreadable, or fails schema validation.
3. WHEN the Agent_Orchestrator plans an action requiring a tool, THE Agent_Orchestrator SHALL look up the tool in the Tool_Registry by its tool identifier before invocation.
4. IF a requested tool is not present in the Tool_Registry, THEN THE Agent_Orchestrator SHALL skip the action, log a warning identifying the missing tool identifier, and record the skipped action in the current scenario's action history.
5. THE Tool_Registry SHALL distinguish between Rust_Primitives (subprocess invocation) and Python-native tools (in-process invocation) via an explicit invocation type field in each tool entry.
6. WHEN a tool entry specifies required capabilities, THE Agent_Orchestrator SHALL compare those capabilities against the active Runtime_Profile before invocation and proceed only if all required capabilities are present.
7. IF the active Runtime_Profile does not satisfy a tool's required capabilities, THEN THE Agent_Orchestrator SHALL skip the tool invocation, log a capability-mismatch warning identifying the missing capabilities, and record the skipped action in the current scenario's action history.
8. WHEN the Agent_Orchestrator invokes a tool, THE Agent_Orchestrator SHALL validate the provided arguments against the tool entry's argument schema and reject invocation with a validation error if any required argument is missing or any argument fails its declared type constraint.

### Requirement 7: Ground-Truth Telemetry Schema and Output

**User Story:** As a detection engineer, I want every Athena agent action to produce labeled ground-truth telemetry in a consistent schema, so that the eval harness can reconcile predictions against known-true attack labels.

#### Acceptance Criteria

1. THE Ground_Truth_Schema SHALL include the following fields: `scenario_id`, `run_id`, `timestamp` (ISO 8601 UTC format), `target`, `payload_family`, `technique`, `expected_result`, `safety_boundary`, `label`, and `artifact_reference`.
2. THE Ground_Truth_Schema `label` field SHALL use one of the enumerated values: `malicious`, `benign_control`, `failed_attack`, `successful_simulation`, `needs_review`.
3. WHEN the Agent_Orchestrator emits a ground-truth record, THE record SHALL be serialized as a single JSON object on one line (JSON Lines format) and appended to a configurable output file path. IF no output path is configured, THEN THE Agent_Orchestrator SHALL write records to stdout.
4. IF the technique associated with an action cannot be mapped to a MITRE ATT&CK technique identifier, THEN THE Ground_Truth_Schema `technique` field SHALL be set to null.
5. THE Ground_Truth_Schema SHALL guarantee round-trip fidelity: serializing any valid record to JSON and deserializing back SHALL produce a field-by-field equivalent object.
6. WHEN multiple ground-truth records are written to the same output file, each record SHALL be independently parseable as a single JSON object occupying exactly one line.

### Requirement 8: Eval Harness for Purple-Team Metrics

**User Story:** As a SOC analyst, I want an evaluation harness that compares ground-truth labels from Athena against AI_Inference_Engine predictions, so that I can measure detection pipeline accuracy with precision, recall, and F1 scores.

#### Acceptance Criteria

1. WHEN provided a set of ground-truth records and corresponding AI_Inference_Engine predictions, THE Eval_Harness SHALL match records by comparing scenario_id and technique fields, and SHALL compute precision, recall, and F1 score from the resulting true-positive, false-positive, and false-negative counts.
2. THE Eval_Harness SHALL output a structured JSON report containing per-technique precision, recall, and F1 score, as well as aggregate (micro-averaged) precision, recall, and F1 score across all techniques.
3. IF a ground-truth record has no matching prediction within a configurable time window (default 300 seconds, configurable between 1 and 86400 seconds), THEN THE Eval_Harness SHALL classify that record as a missed detection (false negative).
4. IF an AI_Inference_Engine prediction has no matching ground-truth record within the same configured time window, THEN THE Eval_Harness SHALL classify that prediction as a false positive.
5. THE Eval_Harness SHALL support filtering metrics by scenario_id, technique, or payload_family.
6. WHEN the Eval_Harness produces a report, THE report SHALL include the model_name, model_version, the configured time window value, the total count of ground-truth records, and the total count of predictions evaluated.
7. IF a ground-truth record matches more than one prediction, THEN THE Eval_Harness SHALL count only the earliest prediction within the time window as a true positive and SHALL classify remaining matching predictions as duplicates excluded from metric computation.
8. IF the input set contains zero ground-truth records or zero predictions, THEN THE Eval_Harness SHALL produce a report with all metric values set to 0 and SHALL include a warning field indicating that one or both input sets were empty.
9. IF a ground-truth record or prediction record is missing a required field (scenario_id, technique, or timestamp), THEN THE Eval_Harness SHALL exclude that record from evaluation and SHALL include it in a skipped_records array in the output report with a reason indicating the missing field.

### Requirement 9: LLM Backend Hardware Abstraction

**User Story:** As a developer working on Apple Silicon or NVIDIA hardware, I want the agent framework to abstract LLM inference backends so that I can run agents on local hardware without code changes.

#### Acceptance Criteria

1. THE Agent_Orchestrator SHALL route inference requests to and receive responses from an Ollama backend for Apple Silicon and cross-platform inference.
2. THE Agent_Orchestrator SHALL route inference requests to and receive responses from a vLLM backend for NVIDIA GPU inference with CUDA acceleration.
3. THE Agent_Orchestrator SHALL route inference requests to and receive responses from a llama.cpp backend for CPU-only and Apple Silicon MLX inference.
4. WHEN the Agent_Orchestrator starts, THE Agent_Orchestrator SHALL validate connectivity to the configured LLM_Backend within 10 seconds and report a startup error identifying the backend URL and failure reason if the backend is unreachable.
5. IF the configured LLM_Backend becomes unreachable during scenario execution, THEN THE Agent_Orchestrator SHALL halt the current scenario and log the failure with the backend identifier and timestamp.
6. THE Agent_Orchestrator SHALL use a common interface for all LLM_Backend implementations so that switching backends requires only configuration changes (environment variable or configuration file).
7. WHEN the Agent_Orchestrator starts, THE Agent_Orchestrator SHALL validate that the configured backend type is one of the supported values (ollama, vllm, llamacpp) and reject startup with a descriptive error if the value is unrecognized.

### Requirement 10: SOC Pipeline Integration

**User Story:** As a detection engineer, I want Athena-generated traffic to flow through the existing SOC pipeline (Suricata → Wazuh → AI_Inference_Engine) without modifications to the SOC components, so that the purple-team loop validates the real detection stack.

#### Acceptance Criteria

1. WHEN Athena_Agent executes an offensive action against a lab target, THE generated network traffic SHALL be captured by Suricata sensors monitoring the lab network segment within 30 seconds of action execution.
2. THE Athena deployment SHALL NOT require modifications to Wazuh agent configuration files, Suricata rule definitions, or AI_Inference_Engine source code to produce events that trigger existing detection logic.
3. WHILE the Purple_Team_Loop is active, THE Eval_Harness SHALL match each ground-truth record from Athena to predictions from the AI_Inference_Engine by pairing records that share the same target identifier and whose timestamps fall within a configurable tolerance window no greater than 60 seconds.
4. THE Athena deployment SHALL label generated traffic using environment variables or metadata so that SOC dashboards can filter training traffic from real alerts by the label value.
5. IF the SOC_Pipeline does not acknowledge ingestion of forwarded events within 30 seconds, THEN THE Agent_Orchestrator SHALL continue executing scenarios and storing ground-truth records locally for later reconciliation.
6. WHEN the SOC_Pipeline becomes reachable after an unavailability period, THE Agent_Orchestrator SHALL forward locally stored ground-truth records to the pipeline within 5 minutes of connectivity restoration.

### Requirement 11: Isolation and Safety Controls

**User Story:** As a platform security engineer, I want Athena agents to enforce strict isolation boundaries and safety controls, so that offensive actions cannot escape the lab environment or affect production systems.

#### Acceptance Criteria

1. THE Agent_Orchestrator SHALL only execute actions against targets listed in an allowlist whose integrity is confirmed by cryptographic signature or hash verification prior to each execution cycle.
2. IF the allowlist is unavailable or fails integrity verification, THEN THE Agent_Orchestrator SHALL refuse all action execution and emit an alert to the audit trail indicating the verification failure reason.
3. THE Agent_Orchestrator SHALL enforce a configurable rate limit on actions per minute, defaulting to 60 actions per minute with a configurable range of 1 to 600 actions per minute.
4. IF the rate limit is exceeded, THEN THE Agent_Orchestrator SHALL queue or reject the excess actions and log a rate-limit breach event to the audit trail.
5. IF a response originates from an IP address or hostname not present in the verified allowlist, THEN THE Agent_Orchestrator SHALL immediately halt all execution, terminate active connections, and log the boundary violation event to the audit trail.
6. THE Athena_Agent container SHALL NOT mount the Docker socket or any hostPath volume by default.
7. WHEN deploying Athena_Agent to Kubernetes, THE deployment manifest SHALL include a securityContext that drops all capabilities and sets `allowPrivilegeEscalation: false`.
8. THE Agent_Orchestrator SHALL log all executed actions with ISO-8601 timestamps, target identifiers, action type, and a completion status of success or failure to an append-only audit trail retained for a minimum of 90 days.

### Requirement 12: Target Environment Support

**User Story:** As a security researcher, I want pre-configured target definitions for OWASP Juice Shop and DVWA, so that I can begin running agent scenarios against established vulnerable applications immediately.

#### Acceptance Criteria

1. THE target environment definitions SHALL include connection parameters specifying host, port, protocol, and base path for OWASP Juice Shop and DVWA.
2. WHEN a target environment is selected, THE Agent_Orchestrator SHALL verify the target is reachable by establishing a TCP connection within a configurable timeout (default 5 seconds) before beginning a scenario.
3. IF the target fails the reachability check, THEN THE Agent_Orchestrator SHALL refuse to start the scenario and log an error identifying the unreachable target and the timeout duration.
4. THE target environment definitions SHALL include metadata mapping known vulnerability categories to OWASP Top 10 classification names to guide agent scenario selection.
5. THE target environment definitions SHALL support custom vulnerable API targets through the same configuration schema (host, port, protocol, base path, vulnerability categories) used for Juice Shop and DVWA.

### Requirement 13: Repository Structure and Build System

**User Story:** As a contributor, I want the `athena-agents` repository to have a clear workspace structure separating Rust crates and Python packages with a unified build and test workflow, so that I can develop in either language with predictable tooling.

#### Acceptance Criteria

1. THE `athena-agents` repository SHALL use a Cargo workspace for Rust crates and a Python project structure (pyproject.toml) for the orchestration layer.
2. THE repository SHALL include a top-level build entry point (Makefile target or executable script) that compiles all Rust binaries and installs Python dependencies, exiting with a non-zero code if any compilation or installation step fails.
3. THE repository SHALL include a top-level test entry point (Makefile target or executable script) that runs Rust unit tests via `cargo test` and Python unit tests via the Python test runner defined in pyproject.toml, exiting with a non-zero code if any test fails.
4. THE build process SHALL place compiled Rust_Primitives binaries in a directory defined by a configurable environment variable (defaulting to `./target/release`), and THE Agent_Orchestrator SHALL resolve binary paths from that same environment variable at runtime.
5. THE repository SHALL include a Dockerfile that produces an agent runner image containing the compiled Rust_Primitives binaries and the Python orchestration environment, using a multi-stage build where the final image does not include build-time toolchains.
6. IF the top-level build entry point is invoked and a required build tool (Rust toolchain or Python interpreter) is not available, THEN THE build process SHALL exit with a non-zero code and print an error message indicating the missing dependency.
