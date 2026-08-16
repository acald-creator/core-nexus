# Requirements Document

## Introduction

Extend the Athena offensive security testing platform with Industrial Control System (ICS) protocol tooling. This adds Modbus TCP and CAN Bus modules as new Rust crates in the existing workspace, integrates them into the tool registry and orchestrator, defines ICS-specific safety controls, and introduces ICS-focused eval metrics. All development targets virtual environments (OpenPLC simulators, GRFICSv2, Linux vcan interfaces) with no real hardware dependency.

## Glossary

- **Athena_Platform**: The AI-driven offensive security testing framework consisting of Rust tool crates, a Python orchestrator, tool registry, and eval harness.
- **Modbus_Module**: The `athena-modbus` Rust crate providing Modbus TCP client operations as a CLI tool.
- **CAN_Module**: The `athena-canbus` Rust crate providing CAN frame crafting, injection, sniffing, replay, and fuzzing over Linux virtual CAN interfaces.
- **Tool_Registry**: The TOML configuration file (`config/tool-registry.toml`) mapping tool identifiers to executables, argument schemas, and capability requirements.
- **Orchestrator**: The Python OPAR-loop agent that coordinates tool execution, allowlist verification, rate limiting, and ground-truth telemetry.
- **Capability_Profile**: A set of named permissions (e.g., `NET_RAW`, `ICS_WRITE`, `CAN_INJECT`) that gate access to dangerous operations.
- **Safe_Range**: A configured minimum/maximum value pair for a specific Modbus register address, defining boundaries the agent must not exceed during write operations.
- **Unit_ID**: A Modbus device address (0–247) identifying a specific device on a Modbus TCP network.
- **Function_Code**: A Modbus operation identifier (1–127) specifying the type of read, write, or diagnostic operation.
- **CAN_Frame**: A Controller Area Network data unit consisting of an arbitration ID (11-bit standard or 29-bit extended) and up to 8 bytes of data.
- **vcan_Interface**: A Linux kernel virtual CAN interface used for development and testing without physical CAN hardware.
- **Ground_Truth_Emitter**: The telemetry subsystem that records labeled action outcomes for the eval harness.
- **Eval_Harness**: The evaluation framework that measures detection metrics and agent performance.

## Requirements

### Requirement 1: Modbus TCP Read Operations

**User Story:** As a security tester, I want to read Modbus registers and coils from a target PLC, so that I can enumerate the state of an industrial control system during reconnaissance.

#### Acceptance Criteria

1. WHEN the Modbus_Module receives a `read-coils` action with a valid target, unit ID, start address, and quantity, THE Modbus_Module SHALL send a Modbus TCP Function Code 01 request and return the coil values as a JSON array on stdout.
2. WHEN the Modbus_Module receives a `read-discrete-inputs` action with valid parameters, THE Modbus_Module SHALL send a Function Code 02 request and return the discrete input values as a JSON array on stdout.
3. WHEN the Modbus_Module receives a `read-holding-registers` action with valid parameters, THE Modbus_Module SHALL send a Function Code 03 request and return the register values as a JSON array of integers on stdout.
4. WHEN the Modbus_Module receives a `read-input-registers` action with valid parameters, THE Modbus_Module SHALL send a Function Code 04 request and return the register values as a JSON array of integers on stdout.
5. IF the target address is unreachable or the connection times out, THEN THE Modbus_Module SHALL output a JSON error to stderr with error category `connection_error` and exit with code 1.
6. IF the Modbus device returns an exception response, THEN THE Modbus_Module SHALL output a JSON error to stderr containing the Modbus exception code and a descriptive message, and exit with code 1.
7. WHEN a read operation completes successfully, THE Modbus_Module SHALL include the unit ID, function code, start address, quantity, and elapsed time in milliseconds in the JSON output.

### Requirement 2: Modbus TCP Write Operations

**User Story:** As a security tester, I want to write values to Modbus registers and coils, so that I can test whether safety-critical controls can be manipulated.

#### Acceptance Criteria

1. WHEN the Modbus_Module receives a `write-coil` action with valid target, unit ID, address, and boolean value, THE Modbus_Module SHALL send a Function Code 05 request and return a confirmation JSON on stdout.
2. WHEN the Modbus_Module receives a `write-register` action with valid target, unit ID, address, and 16-bit integer value, THE Modbus_Module SHALL send a Function Code 06 request and return a confirmation JSON on stdout.
3. WHEN the Modbus_Module receives a `write-multiple-coils` action with valid target, unit ID, start address, and array of boolean values, THE Modbus_Module SHALL send a Function Code 15 request and return a confirmation JSON on stdout.
4. WHEN the Modbus_Module receives a `write-multiple-registers` action with valid target, unit ID, start address, and array of 16-bit integer values, THE Modbus_Module SHALL send a Function Code 16 request and return a confirmation JSON on stdout.
5. IF the active Capability_Profile does not include the `ICS_WRITE` capability, THEN THE Orchestrator SHALL refuse to execute any Modbus write operation and emit a `needs_review` ground-truth record.
6. IF a write value exceeds the configured Safe_Range for the target register address, THEN THE Modbus_Module SHALL reject the operation with a JSON error to stderr containing `safety_boundary_violation` and exit with code 1.

### Requirement 3: Modbus Unit ID Enumeration

**User Story:** As a security tester, I want to enumerate which Unit IDs respond on a Modbus TCP endpoint, so that I can discover all devices accessible through a single gateway.

#### Acceptance Criteria

1. WHEN the Modbus_Module receives an `enumerate` action with a valid target, THE Modbus_Module SHALL send read requests to Unit IDs in the range 1–247 and return a JSON array of responding Unit IDs on stdout.
2. WHEN a Unit ID does not respond within the configured timeout, THE Modbus_Module SHALL treat that Unit ID as non-responding and continue scanning.
3. WHEN enumeration completes, THE Modbus_Module SHALL include the total scan duration, number of responsive units, and the timeout value used in the JSON output.

### Requirement 4: Modbus Fuzzing

**User Story:** As a security tester, I want to fuzz arbitrary Modbus function codes with random payloads, so that I can discover implementation vulnerabilities in PLC firmware.

#### Acceptance Criteria

1. WHEN the Modbus_Module receives a `fuzz` action with target, unit ID, seed, and iteration count, THE Modbus_Module SHALL generate deterministic random payloads using the provided seed and send them as raw Modbus requests.
2. WHEN a fuzz iteration completes, THE Modbus_Module SHALL record the function code used, payload size, and whether the device responded or timed out.
3. WHEN all fuzz iterations complete, THE Modbus_Module SHALL output a JSON summary including seed, iterations completed, elapsed time, and an array of per-iteration records on stdout.
4. THE Modbus_Module SHALL generate function codes in the range 1–127 during fuzzing.

### Requirement 5: CAN Bus Frame Crafting

**User Story:** As a security tester, I want to craft arbitrary CAN frames with specified IDs and data, so that I can prepare payloads for injection testing.

#### Acceptance Criteria

1. WHEN the CAN_Module receives a `craft` action with a standard arbitration ID (0–0x7FF) and data bytes (0–8 bytes), THE CAN_Module SHALL produce a valid standard CAN frame and output its hex representation as JSON on stdout.
2. WHEN the CAN_Module receives a `craft` action with an extended arbitration ID (0–0x1FFFFFFF) and the `--extended` flag, THE CAN_Module SHALL produce a valid extended CAN frame and output its hex representation as JSON on stdout.
3. IF the arbitration ID exceeds the valid range for the selected frame type, THEN THE CAN_Module SHALL output a JSON error to stderr with `validation_error` and exit with code 1.
4. IF the data length exceeds 8 bytes, THEN THE CAN_Module SHALL output a JSON error to stderr with `validation_error` and exit with code 1.

### Requirement 6: CAN Bus Injection and Sniffing

**User Story:** As a security tester, I want to inject CAN frames onto a virtual CAN interface and sniff frames from it, so that I can test automotive and ICS CAN-based systems.

#### Acceptance Criteria

1. WHEN the CAN_Module receives an `inject` action with a valid frame and interface name, THE CAN_Module SHALL write the frame to the specified vcan_Interface and output a confirmation JSON on stdout.
2. IF the active Capability_Profile does not include the `CAN_INJECT` capability, THEN THE Orchestrator SHALL refuse to execute any CAN injection operation and emit a `needs_review` ground-truth record.
3. WHEN the CAN_Module receives a `sniff` action with an interface name and duration, THE CAN_Module SHALL capture frames from the vcan_Interface for the specified duration and output them as a JSON array on stdout.
4. IF the specified vcan_Interface does not exist or is not accessible, THEN THE CAN_Module SHALL output a JSON error to stderr with `interface_error` and exit with code 1.

### Requirement 7: CAN Bus Replay and Fuzzing

**User Story:** As a security tester, I want to replay captured CAN traffic and fuzz CAN frame IDs and data, so that I can test system behavior under adversarial conditions.

#### Acceptance Criteria

1. WHEN the CAN_Module receives a `replay` action with a capture file path and interface name, THE CAN_Module SHALL re-transmit the captured frames at their original timing intervals onto the specified vcan_Interface.
2. WHEN the CAN_Module receives a `fuzz` action with interface, seed, iteration count, and optional ID range, THE CAN_Module SHALL generate deterministic random CAN frames using the provided seed and transmit them.
3. WHEN CAN fuzzing completes, THE CAN_Module SHALL output a JSON summary including seed, iterations completed, ID range covered, elapsed time, and frame count on stdout.
4. IF the active Capability_Profile does not include the `CAN_INJECT` capability, THEN THE Orchestrator SHALL refuse to execute CAN replay or fuzz operations.

### Requirement 8: Tool Registry Integration

**User Story:** As the orchestrator system, I want ICS tools registered with proper argument schemas, so that the OPAR loop can validate and invoke them like existing tools.

#### Acceptance Criteria

1. THE Tool_Registry SHALL include entries for `modbus-read`, `modbus-write`, `modbus-fuzz`, and `modbus-enumerate` tools pointing to the `athena-modbus` binary.
2. THE Tool_Registry SHALL include entries for `canbus-craft`, `canbus-inject`, `canbus-sniff`, and `canbus-fuzz` tools pointing to the `athena-canbus` binary.
3. THE Tool_Registry SHALL define argument schemas with validation constraints: Modbus addresses 0–65535, function codes 1–127, CAN standard IDs 0–0x7FF, CAN extended IDs 0–0x1FFFFFFF.
4. THE Tool_Registry SHALL declare `ICS_WRITE` as a required capability for `modbus-write`.
5. THE Tool_Registry SHALL declare `CAN_INJECT` as a required capability for `canbus-inject`, `canbus-fuzz`, and `canbus-sniff` in write mode.

### Requirement 9: ICS Safety Controls

**User Story:** As a platform operator, I want ICS-specific safety controls, so that the autonomous agent cannot cause unintended damage to simulated or real industrial processes.

#### Acceptance Criteria

1. WHILE an ICS target is active, THE Orchestrator SHALL apply a default rate limit of 10 actions per minute instead of the standard 60.
2. WHERE a Safe_Range configuration exists for a target register, THE Modbus_Module SHALL validate all write values against the configured minimum and maximum before transmission.
3. IF the Orchestrator detects a boundary violation (write outside Safe_Range or action without required capability), THEN THE Orchestrator SHALL emit a ground-truth record with label `needs_review` and halt the current action.
4. THE Orchestrator SHALL load ICS rate-limit defaults from the target configuration, allowing per-target override of the default 10 actions/minute.
5. WHEN a Modbus write is blocked by a Safe_Range violation, THE Modbus_Module SHALL include the attempted value, the register address, and the configured safe minimum and maximum in the error output.

### Requirement 10: ICS Target Definitions

**User Story:** As a security tester, I want pre-configured ICS target definitions, so that I can quickly set up engagements against common ICS lab environments.

#### Acceptance Criteria

1. THE Athena_Platform SHALL include a target configuration for OpenPLC with Modbus TCP on port 502, including known register maps and Safe_Range definitions.
2. THE Athena_Platform SHALL include a target configuration for GRFICSv2 chemical process simulator with appropriate protocol metadata and vulnerability categories.
3. THE Athena_Platform SHALL include a target configuration for a virtual CAN bus lab environment specifying the vcan_Interface name and expected ID ranges.
4. WHEN a target configuration is loaded, THE Orchestrator SHALL apply the ICS-specific rate limits and capability requirements defined in that configuration.

### Requirement 11: ICS Eval Metrics

**User Story:** As a platform operator, I want ICS-specific evaluation metrics, so that I can measure the effectiveness and safety of autonomous ICS testing.

#### Acceptance Criteria

1. WHEN an ICS engagement completes, THE Eval_Harness SHALL report Modbus function code coverage as a percentage of tested function codes out of the set exercised.
2. WHEN an ICS engagement completes, THE Eval_Harness SHALL report register coverage as a percentage of the target register address space that was read or written.
3. WHEN a CAN fuzzing engagement completes, THE Eval_Harness SHALL report CAN arbitration ID coverage as a percentage of the configured ID range that was exercised.
4. THE Eval_Harness SHALL report safety boundary compliance as the ratio of actions that stayed within configured Safe_Ranges to total write actions attempted.
5. WHEN a safety boundary violation occurs, THE Eval_Harness SHALL record the violation details including register address, attempted value, and configured bounds.

### Requirement 12: CLI and Output Conventions

**User Story:** As a developer, I want ICS tools to follow existing Athena CLI and output conventions, so that they integrate seamlessly with the orchestrator and eval harness.

#### Acceptance Criteria

1. THE Modbus_Module SHALL accept arguments via long-form CLI flags (e.g., `--target`, `--action`, `--unit-id`, `--address`).
2. THE CAN_Module SHALL accept arguments via long-form CLI flags (e.g., `--interface`, `--action`, `--id`, `--data`).
3. THE Modbus_Module SHALL output successful results as a single JSON object on stdout.
4. THE CAN_Module SHALL output successful results as a single JSON object on stdout.
5. IF a validation error occurs in either module, THEN THE module SHALL output a JSON object with `error` and `message` fields to stderr and exit with code 1.
6. THE Modbus_Module SHALL use `clap` for argument parsing and `serde`/`serde_json` for output serialization, consistent with existing Athena crates.
7. THE CAN_Module SHALL use `clap` for argument parsing and `serde`/`serde_json` for output serialization, consistent with existing Athena crates.

### Requirement 13: Connection Handling and Timeouts

**User Story:** As a security tester, I want ICS tools to handle connection issues gracefully, so that slow or unresponsive ICS devices do not cause tool hangs or crashes.

#### Acceptance Criteria

1. THE Modbus_Module SHALL accept a `--timeout-ms` flag with a default of 5000ms and a valid range of 500–60000ms.
2. WHEN a Modbus TCP connection is not established within the timeout, THE Modbus_Module SHALL output a JSON error with `connection_timeout` to stderr and exit with code 1.
3. WHEN a Modbus response is not received within the timeout after a request is sent, THE Modbus_Module SHALL output a JSON error with `response_timeout` to stderr and exit with code 1.
4. THE CAN_Module SHALL accept a `--timeout-ms` flag for sniff duration with a default of 10000ms and a valid range of 1000–300000ms.
5. WHEN the CAN sniff duration elapses, THE CAN_Module SHALL stop capturing and output the collected frames.

### Requirement 14: Shared ICS Types in athena-common

**User Story:** As a developer, I want shared ICS data types in the common crate, so that output structures are consistent and reusable across ICS tools.

#### Acceptance Criteria

1. THE athena-common crate SHALL define serializable types for Modbus read results, write confirmations, enumeration results, and fuzzer summaries.
2. THE athena-common crate SHALL define serializable types for CAN frame representations, injection confirmations, sniff captures, and fuzz summaries.
3. THE athena-common crate SHALL define an `IcsProtocol` enum distinguishing Modbus TCP from CAN Bus for use in ground-truth records.
4. FOR ALL ICS result types defined in athena-common, serializing to JSON and deserializing back SHALL produce an equivalent value (round-trip property).
