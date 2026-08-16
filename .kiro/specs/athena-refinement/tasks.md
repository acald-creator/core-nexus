# Implementation Plan: Athena Refinement

## Overview

This plan implements the Athena subsystem refinement in two tracks: (1) modernizing the `nexus-athena` Docker image into a multi-stage, multi-platform build with tiered runtime profiles and Kubernetes NetworkPolicies, and (2) creating the `athena-agents` repository with an AI offensive agent framework (Python orchestrator + Rust primitives), ground-truth telemetry, eval harness, and LLM backend abstraction. Tasks are ordered for incremental development — foundational infrastructure first, then application logic, then integration and safety controls.

## Tasks

- [x] 1. Modernize nexus-athena Docker image
  - [x] 1.1 Refactor Dockerfile into multi-stage multi-platform build
    - Replace the existing single-stage `Dockerfile` with a multi-stage Dockerfile producing `athena-core` and `athena-full` targets
    - Use `kalilinux/kali-rolling` as the base image (replacing `kali-bleeding-edge`)
    - Stage 1 (`athena-core`): nmap, python3, python3-pip, python3-scapy, git, curl, wget, netcat-openbsd, iproute2, dnsutils, tcpdump, ca-certificates, vim
    - Stage 2 (`athena-full` FROM athena-core): metasploit-framework, wireshark (tshark), radare2 pinned to `RADARE2_REF`
    - Remove all VOLUME directives (`/var/run`, `/var/lib/docker/volumes`, `/nexus-bucket`)
    - Add non-root user `athena` (UID 1000) as default execution identity
    - Add OCI labels documenting required capabilities per target
    - Support `linux/amd64` and `linux/arm64` via `docker buildx` and `ARG TARGETPLATFORM`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [x] 1.2 Add exploit-lab runtime profile to Docker Compose
    - Add `athena.exploit-lab` service to `deploy/compose/athena-profiles.yml`
    - Set `cap_add: [NET_ADMIN, NET_RAW, SYS_PTRACE]`, `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`
    - Gate behind `profiles: [exploit-lab]`
    - Attach only to `athena_lab` network
    - _Requirements: 2.1, 2.3, 2.6_

  - [x] 1.3 Create exploit-lab Kubernetes Deployment manifest
    - Create `deploy/kubernetes/base/athena-exploit-lab.yaml`
    - Set `replicas: 0`, require explicit `kubectl scale` to activate
    - Add annotations documenting required capabilities: `nexus-athena/required-capabilities: "NET_ADMIN,NET_RAW,SYS_PTRACE"`
    - Set securityContext: `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `capabilities.add: [NET_ADMIN, NET_RAW, SYS_PTRACE]`
    - Use image `phoenixvlabs/nexus-athena:full-latest`
    - _Requirements: 2.2, 2.4, 2.5_

  - [x] 1.4 Create Kubernetes NetworkPolicies for Athena namespace isolation
    - Create `deploy/kubernetes/base/network-policy-default-deny.yaml`: deny all ingress/egress except DNS (UDP 53 to kube-dns in kube-system)
    - Create `deploy/kubernetes/base/network-policy-lab-egress.yaml`: allow egress to pods with `nexus-lab-target: "true"` in namespaces with `nexus-lab-network: "true"`, plus DNS
    - Create `deploy/kubernetes/base/network-policy-soc-deny.yaml`: explicit deny to namespaces with `nexus-zone: soc`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 2. Checkpoint - Verify nexus-athena image modernization
  - Ensure Dockerfile builds both targets for at least one platform
  - Ensure Kubernetes manifests pass `kubectl apply --dry-run=client`
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Set up athena-agents repository structure and build system
  - [x] 3.1 Initialize repository with workspace structure
    - Create top-level `Cargo.toml` workspace with `members = ["crates/*"]`
    - Create `pyproject.toml` for the Python orchestrator package
    - Create directory structure: `crates/`, `orchestrator/`, `eval/`, `config/`, `tests/`, `docs/`
    - Create `Makefile` with targets: `build`, `test`, `lint`, `fmt`, `image`
    - Build target: compile Rust + install Python deps; exit non-zero on failure
    - Test target: `cargo test` + `pytest`; exit non-zero on failure
    - Print missing dependency error if Rust toolchain or Python not available
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.6_

  - [x] 3.2 Create shared Rust types crate (`athena-common`)
    - Create `crates/athena-common/Cargo.toml` with serde, serde_json dependencies
    - Implement shared JSON output types: `ScanResult`, `FuzzerSummary`, `CraftResult`
    - Implement shared error output type: `ErrorOutput { error: String, message: String }`
    - Implement CLI validation error formatting to JSON on stderr
    - _Requirements: 5.4, 13.1_

  - [ ]* 3.3 Write property tests for Rust primitives input validation error format
    - **Property 11: Rust Primitives Input Validation Error Format**
    - For any invalid CLI input (port out of range, missing required argument, invalid type), verify non-zero exit code and JSON stderr with `error` and `message` fields
    - Use `proptest` crate with minimum 100 iterations
    - **Validates: Requirements 5.4**

  - [x] 3.4 Implement async TCP port scanner (`athena-scanner`)
    - Create `crates/athena-scanner/Cargo.toml` with tokio, clap, athena-common dependencies
    - Implement CLI: `--target`, `--start-port`, `--end-port`, `--concurrency` (default 1024, range 1-65535), `--timeout-ms` (default 3000, range 100-30000)
    - Implement async scanning with tokio semaphore-bounded connection pool
    - Output JSON to stdout: `{ target, ports: [{port, status}], scan_duration_ms }`
    - Validate port range (start <= end, both 1-65535); exit 1 with JSON error on invalid input
    - Build targets: `x86_64-unknown-linux-musl`, `aarch64-unknown-linux-musl`
    - _Requirements: 5.1, 5.5, 5.6, 5.7_

  - [ ]* 3.5 Write property tests for port scanner output completeness
    - **Property 2: Port Scanner Output Completeness**
    - For any valid target and port range [start, end], output SHALL contain exactly `end - start + 1` entries each with port number and status
    - Use `proptest` crate with minimum 100 iterations
    - **Validates: Requirements 5.1**

  - [x] 3.6 Implement protocol fuzzer (`athena-fuzzer`)
    - Create `crates/athena-fuzzer/Cargo.toml` with tokio, clap, rand_xoshiro, athena-common dependencies
    - Implement CLI: `--target`, `--protocol` (http|tcp|dns), `--seed` (u64), `--iterations` (default 1000, range 1-1000000)
    - Use xoshiro256++ PRNG seeded from CLI argument for deterministic mutations
    - Output mutation records as JSON to stdout
    - On completion or connection failure: output summary JSON with `iterations_completed` and `elapsed_ms`
    - _Requirements: 5.2, 5.8_

  - [ ]* 3.7 Write property tests for fuzzer determinism and summary completeness
    - **Property 3: Fuzzer Deterministic Reproducibility**
    - For any given seed, protocol, and iteration count, two invocations produce identical mutation sequences
    - **Property 4: Fuzzer Summary Completeness**
    - For any completed execution with iteration count N, summary reports `iterations_completed <= N` and non-negative `elapsed_ms`
    - Use `proptest` crate with minimum 100 iterations
    - **Validates: Requirements 5.2, 5.8**

  - [x] 3.8 Implement packet crafter (`athena-crafter`)
    - Create `crates/athena-crafter/Cargo.toml` with clap, athena-common dependencies
    - Implement CLI: `--protocol` (tcp|udp|icmp), `--src-port`, `--dst-port`, `--payload` (hex-string), `--flags` (optional)
    - Output JSON to stdout: `{ protocol, total_length_bytes, payload_hex }`
    - Validate all inputs; exit 1 with JSON error on failure
    - _Requirements: 5.3, 5.4, 5.5_

- [x] 4. Checkpoint - Verify Rust primitives build and test
  - Ensure `cargo build --release` compiles all crates
  - Ensure `cargo test` passes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Python orchestrator core
  - [x] 5.1 Define orchestrator interfaces and data models
    - Create `orchestrator/__init__.py`, `orchestrator/interfaces.py`
    - Implement dataclasses: `TargetState`, `ActionSpec`, `ActionResult`, `ReflectSummary`
    - Implement `GroundTruthRecord` dataclass with all schema fields (scenario_id, run_id, timestamp, target, payload_family, technique, expected_result, safety_boundary, label, artifact_reference)
    - Implement `GroundTruthLabel` enum: malicious, benign_control, failed_attack, successful_simulation, needs_review
    - _Requirements: 4.1, 7.1, 7.2_

  - [x] 5.2 Implement ground-truth telemetry emitter
    - Create `orchestrator/ground_truth.py`
    - Implement JSON Lines serialization (one JSON object per line)
    - Support configurable output path via `ATHENA_GT_OUTPUT` env var; default to stdout
    - Ensure each record is independently parseable
    - _Requirements: 7.3, 7.4, 7.5, 7.6_

  - [ ]* 5.3 Write property test for ground-truth serialization round trip
    - **Property 1: Ground-Truth Serialization Round Trip**
    - For any valid `GroundTruthRecord`, serialize to JSON and deserialize back; verify field-by-field equivalence
    - Use `hypothesis` library with minimum 100 iterations
    - **Validates: Requirements 7.5**

  - [x] 5.4 Implement allowlist verification
    - Create `orchestrator/allowlist.py`
    - Implement `AllowlistEntry` dataclass: host, port_range, protocol, label
    - Implement `verify_allowlist(path, expected_hash)`: load JSON, compute SHA-256, compare against expected hash
    - Raise `AllowlistError` on verification failure
    - _Requirements: 4.2, 4.3, 11.1, 11.2_

  - [ ]* 5.5 Write property test for allowlist rejection
    - **Property 8: Allowlist Rejection**
    - For any target not in the verified allowlist, orchestrator refuses execution and action history remains empty
    - Use `hypothesis` library with minimum 100 iterations
    - **Validates: Requirements 4.2, 4.3, 11.1**

  - [x] 5.6 Implement token-bucket rate limiter
    - Create `orchestrator/rate_limiter.py`
    - Implement `RateLimiter` class with configurable actions_per_minute (range 1-600, default 60)
    - Token-bucket algorithm with `bucket_size` and `refill_rate` (tokens per second)
    - Queue or reject excess actions; log rate-limit breach events
    - _Requirements: 11.3, 11.4_

  - [ ]* 5.7 Write property test for rate limiter invariant
    - **Property 9: Rate Limiter Invariant**
    - For any N requests in one minute where N > R (configured limit), at most R actions executed
    - Use `hypothesis` library with minimum 100 iterations
    - **Validates: Requirements 11.3, 11.4**

  - [x] 5.8 Implement Tool Registry loader and validator
    - Create `orchestrator/tool_registry.py`
    - Implement Pydantic models: `ToolArg`, `ToolEntry` matching the TOML schema
    - Load and validate `config/tool-registry.toml` at startup
    - Reject startup with descriptive error if file missing, unreadable, or invalid
    - Validate tool arguments at invocation time against declared schema
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.8_

  - [ ]* 5.9 Write property test for tool registry argument validation
    - **Property 5: Tool Registry Argument Validation**
    - For any tool entry and arguments where a required arg is missing or violates type constraints, orchestrator rejects invocation with validation error
    - Use `hypothesis` library with minimum 100 iterations
    - **Validates: Requirements 6.8**

- [x] 6. Checkpoint - Verify orchestrator core modules
  - Ensure `pytest` passes for ground-truth, allowlist, rate limiter, and tool registry modules
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Agent Orchestrator execution cycle
  - [x] 7.1 Implement observe/plan/act/reflect loop
    - Create `orchestrator/agent.py` with `AgentOrchestrator` class
    - Implement `run_scenario(scenario: ScenarioConfig) -> ScenarioResult`
    - Observe: produce `TargetState` snapshot
    - Plan: select technique/tool via LLM + Tool_Registry
    - Act: execute action, emit ground-truth record
    - Reflect: evaluate result, append summary to action history
    - Maintain in-memory action history accessible to reflect phase
    - _Requirements: 4.1, 4.5, 4.7_

  - [x] 7.2 Implement safety controls and scenario lifecycle
    - Integrate allowlist verification before each execution cycle
    - Integrate rate limiter into act phase
    - Enforce configurable max actions per scenario (range 1-1000); halt with `limit-reached` reason
    - On failure (target unreachable, tool error, LLM timeout): halt, log, emit `needs_review` record
    - Capability checking: compare tool required_capabilities against active profile before invocation
    - Skip tool if capability mismatch; log warning and record in action history
    - _Requirements: 4.2, 4.3, 4.6, 4.8, 6.4, 6.6, 6.7, 11.1, 11.5_

  - [ ]* 7.3 Write property test for action limit termination
    - **Property 10: Action Limit Termination**
    - For any configured max M (1 <= M <= 1000), orchestrator executes at most M actions before halting; final record includes termination reason
    - Use `hypothesis` library with minimum 100 iterations
    - **Validates: Requirements 4.6**

  - [x] 7.4 Implement audit trail logging
    - Log all executed actions with ISO-8601 timestamps, target, action_type, tool_id, status (success/failure)
    - Append-only audit trail format (JSON Lines)
    - _Requirements: 11.8_

- [x] 8. Implement LLM Backend abstraction
  - [x] 8.1 Define LLM interface and implement backends
    - Create `orchestrator/llm/__init__.py`, `orchestrator/llm/interface.py`
    - Define `LLMBackend` protocol: `generate(prompt, max_tokens) -> str`, `health_check() -> bool`, `backend_id` property
    - Implement `OllamaBackend` in `orchestrator/llm/ollama.py` (HTTP client for Ollama REST API)
    - Implement `VLLMBackend` in `orchestrator/llm/vllm.py` (OpenAI-compatible API)
    - Implement `LlamaCppBackend` in `orchestrator/llm/llamacpp.py` (llama.cpp server API)
    - _Requirements: 9.1, 9.2, 9.3, 9.6_

  - [x] 8.2 Implement backend configuration and startup validation
    - Create `config/llm.toml` with backend type, URL, model, timeout fields
    - Parse `type` field; reject if not in {ollama, vllm, llamacpp}
    - Call `health_check()` with 10-second timeout at startup
    - Report URL and failure reason if unreachable; exit non-zero
    - On mid-scenario failure: halt scenario, log with backend_id and timestamp
    - _Requirements: 9.4, 9.5, 9.7_

- [x] 9. Implement Eval Harness
  - [x] 9.1 Implement matching algorithm and metrics computation
    - Create `eval/__init__.py`, `eval/harness.py`
    - Implement `match_records(ground_truth, predictions, time_window_seconds)` with algorithm:
      1. Sort by timestamp
      2. Match by scenario_id + technique within time window
      3. Earliest prediction wins (one-to-one matching)
      4. Unmatched GT = false negatives; unmatched predictions = false positives
    - Compute per-technique: TP, FP, FN, precision, recall, F1
    - Compute aggregate micro-averaged precision, recall, F1
    - Support configurable time window (default 300s, range 1-86400s)
    - _Requirements: 8.1, 8.3, 8.4, 8.7_

  - [x] 9.2 Implement report generation and filtering
    - Create `eval/report.py`
    - Output structured JSON report with: model_name, model_version, time_window, total counts, per_technique metrics, aggregate metrics, skipped_records, warning, duplicates_excluded
    - Support filtering by scenario_id, technique, or payload_family
    - Handle missing required fields: exclude record, add to skipped_records with reason
    - Handle empty inputs: all metrics = 0, set warning field
    - _Requirements: 8.2, 8.5, 8.6, 8.8, 8.9_

  - [ ]* 9.3 Write property tests for eval harness metric consistency
    - **Property 6: Eval Harness Metric Consistency**
    - For any TP, FP, FN values: precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2*P*R/(P+R) (or 0 when denominator is 0)
    - **Validates: Requirements 8.1**

  - [ ]* 9.4 Write property test for eval harness one-to-one matching
    - **Property 7: Eval Harness One-to-One Matching**
    - For any GT record matching multiple predictions, only earliest counted as TP; sum of TP + FP + FN + duplicates = total GT + total predictions
    - Use `hypothesis` library with minimum 100 iterations
    - **Validates: Requirements 8.7**

  - [ ]* 9.5 Write property test for eval harness empty input handling
    - **Property 12: Eval Harness Empty Input Handling**
    - For any evaluation where GT or predictions is empty, all metrics = 0 and warning field present
    - Use `hypothesis` library with minimum 100 iterations
    - **Validates: Requirements 8.8**

- [x] 10. Checkpoint - Verify orchestrator + eval harness integration
  - Ensure all Python tests pass (`pytest`)
  - Ensure all Rust tests pass (`cargo test`)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement configuration and target environments
  - [x] 11.1 Create Tool Registry configuration file
    - Create `config/tool-registry.toml` with entries for: port-scanner, protocol-fuzzer, packet-crafter, nmap-scan, scapy-craft
    - Each entry includes: executable/module, invocation type, required_capabilities, description, args schema
    - Use `${ATHENA_BIN_DIR}` for Rust binary paths (configurable via env var, default `./target/release`)
    - _Requirements: 6.1, 6.5, 13.4_

  - [x] 11.2 Create target environment definitions
    - Create `config/targets/juice-shop.toml` with host, port, protocol, base_path, timeout, vulnerability categories, OWASP Top 10 mappings
    - Create `config/targets/dvwa.toml` with same schema
    - Schema supports custom targets with same fields
    - _Requirements: 12.1, 12.4, 12.5_

  - [x] 11.3 Implement target reachability verification
    - In `orchestrator/agent.py`, verify target reachable via TCP within configurable timeout (default 5s) before starting scenario
    - Refuse scenario and log error if target unreachable
    - _Requirements: 12.2, 12.3_

  - [x] 11.4 Create allowlist configuration
    - Create `config/allowlist.json` with entries for juice-shop and dvwa lab targets
    - Each entry: host, port_range, protocol, label
    - Document expected hash or signature mechanism
    - _Requirements: 11.1_

- [x] 12. Implement SOC pipeline integration and traffic labeling
  - [x] 12.1 Implement traffic labeling and metadata
    - Set `X-Athena-Scenario-Id` header on HTTP-based attack traffic
    - Set `ATHENA_SCENARIO_LABEL` environment variable for tool invocations
    - Enable SOC dashboards to filter training traffic by label
    - _Requirements: 10.2, 10.4_

  - [x] 12.2 Implement local buffering and pipeline resilience
    - If SOC pipeline doesn't acknowledge within 30 seconds, continue execution and store GT records locally
    - On pipeline recovery, forward locally stored records within 5 minutes
    - _Requirements: 10.5, 10.6_

- [x] 13. Create agent runner Docker image
  - [x] 13.1 Write multi-stage Dockerfile for athena-agents
    - Stage 1 (rust-builder): Compile Rust binaries as static musl binaries
    - Stage 2 (python-env): Install orchestrator Python package
    - Stage 3 (runner): Copy Rust binaries from builder, copy Python env, no build toolchains
    - Run as non-root `athena` user
    - Include securityContext annotations: drop all capabilities, `allowPrivilegeEscalation: false`
    - _Requirements: 13.5, 11.6, 11.7_

- [x] 14. Final checkpoint - Ensure all tests pass
  - Run `make test` (cargo test + pytest)
  - Verify `make build` succeeds
  - Verify `make image` produces the agent runner image
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The nexus-athena image work (tasks 1-2) can proceed in parallel with athena-agents repo setup (tasks 3+)
- Rust primitives and Python orchestrator modules are independent until wired together in task 7
- SOC pipeline integration (task 12) is the final piece closing the purple-team feedback loop

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "3.2"] },
    { "id": 2, "tasks": ["3.3", "3.4", "3.6", "3.8", "5.1"] },
    { "id": 3, "tasks": ["3.5", "3.7", "5.2", "5.4", "5.6", "5.8"] },
    { "id": 4, "tasks": ["5.3", "5.5", "5.7", "5.9", "8.1"] },
    { "id": 5, "tasks": ["7.1", "8.2", "9.1", "11.1", "11.2", "11.4"] },
    { "id": 6, "tasks": ["7.2", "7.4", "9.2", "11.3"] },
    { "id": 7, "tasks": ["7.3", "9.3", "9.4", "9.5", "12.1"] },
    { "id": 8, "tasks": ["12.2", "13.1"] }
  ]
}
```
