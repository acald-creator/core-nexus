# Implementation Plan: Athena ICS Tooling

## Overview

Extend the Athena offensive security platform with Modbus TCP and CAN Bus modules. Implementation proceeds in layers: shared types first, then Modbus core logic, CAN core logic, orchestrator integration (safety controls + tool registry), eval metrics, and target configurations. Each layer builds on the previous and includes its own validation.

## Tasks

- [x] 1. Add shared ICS types to athena-common
  - [x] 1.1 Add ICS type definitions to `crates/athena-common/src/lib.rs`
    - Add `IcsProtocol` enum (ModbusTcp, CanBus) with serde rename
    - Add `ModbusReadResult`, `ModbusWriteResult`, `ModbusEnumerateResult` structs
    - Add `ModbusFuzzSummary` and `ModbusFuzzRecord` structs
    - Add `CanIdType` enum (Standard, Extended)
    - Add `CanCraftResult`, `CanInjectResult`, `CanSniffResult`, `CanSniffFrame`, `CanFuzzSummary` structs
    - All types derive `Debug, Clone, Serialize, Deserialize, PartialEq, Eq`
    - _Requirements: 14.1, 14.2, 14.3_

  - [ ]* 1.2 Write property tests for ICS type serialization round-trip
    - Add `proptest` as dev-dependency to `athena-common`
    - **Property 1: Modbus ICS Type Serialization Round-Trip**
    - **Property 2: CAN ICS Type Serialization Round-Trip**
    - **Validates: Requirements 14.4**

- [x] 2. Implement Modbus TCP frame encoding/decoding
  - [x] 2.1 Create `crates/athena-modbus/` crate with Cargo.toml
    - Add workspace member in root `Cargo.toml`
    - Dependencies: `athena-common`, `tokio`, `clap`, `serde`, `serde_json`, `rand`, `rand_xoshiro`
    - Dev-dependencies: `proptest`, `tokio-test`
    - _Requirements: 12.6_

  - [x] 2.2 Implement MBAP frame encoding/decoding in `src/frame.rs`
    - Implement `MbapHeader` struct (transaction_id, protocol_id, length, unit_id)
    - Implement `ModbusRequest` struct (header + function_code + data)
    - Implement `encode_request(&ModbusRequest) -> Vec<u8>` (big-endian serialization)
    - Implement `decode_response(bytes) -> Result<ModbusResponse, ModbusError>`
    - Handle Modbus exception responses (function code with high bit set)
    - Transaction ID generation (sequential u16 with wrapping)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 1.7_

  - [ ]* 2.3 Write property test for MBAP frame round-trip
    - **Property 3: Modbus MBAP Frame Encoding Round-Trip**
    - Generate random valid requests (unit_id 1–247, function_code 1–127, data 0–252 bytes)
    - Verify encode then decode produces equivalent request
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 12.3**

- [x] 3. Implement Modbus TCP client and read operations
  - [x] 3.1 Implement async Modbus TCP client in `src/client.rs`
    - Implement `ModbusClient::connect(target, timeout_ms) -> Result<Self>`
    - Implement `send_request(&mut self, request) -> Result<ModbusResponse>`
    - Use `tokio::net::TcpStream` for async TCP
    - Use `tokio::time::timeout` for connect and response timeouts
    - Handle connection errors → `connection_error` / `connection_timeout`
    - Handle response timeouts → `response_timeout`
    - _Requirements: 1.5, 13.1, 13.2, 13.3_

  - [x] 3.2 Implement Modbus read operations in `src/lib.rs`
    - Implement `read_coils(client, unit_id, address, quantity) -> Result<ModbusReadResult>`
    - Implement `read_discrete_inputs(...)` (FC 02)
    - Implement `read_holding_registers(...)` (FC 03)
    - Implement `read_input_registers(...)` (FC 04)
    - Build proper PDU for each function code
    - Parse response data into values vector
    - Include elapsed_ms timing
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.7_

  - [ ]* 3.3 Write unit tests for Modbus read operations
    - Test PDU construction for FC 01, 02, 03, 04
    - Test response parsing for each function code
    - Test exception response handling (FC + 0x80)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

- [x] 4. Implement Modbus write operations and safety validation
  - [x] 4.1 Implement safe-range validation in `src/lib.rs`
    - Implement `SafeRange { address: u16, min: u16, max: u16 }`
    - Implement `validate_write_value(address, value, safe_ranges) -> Result<(), SafetyError>`
    - Return error with attempted value, address, configured min/max on violation
    - _Requirements: 2.6, 9.2, 9.5_

  - [ ]* 4.2 Write property test for safe-range enforcement
    - **Property 6: Safe Range Boundary Enforcement**
    - Generate random (address, value, min, max) tuples
    - Verify values in [min, max] pass, values outside fail with correct error fields
    - **Validates: Requirements 2.6, 9.2, 9.5**

  - [x] 4.3 Implement Modbus write operations in `src/lib.rs`
    - Implement `write_coil(client, unit_id, address, value, safe_ranges)` (FC 05)
    - Implement `write_register(client, unit_id, address, value, safe_ranges)` (FC 06)
    - Implement `write_multiple_coils(client, unit_id, address, values, safe_ranges)` (FC 15)
    - Implement `write_multiple_registers(client, unit_id, address, values, safe_ranges)` (FC 16)
    - Check safe_ranges before building frame; reject if violated
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

  - [ ]* 4.4 Write unit tests for Modbus write operations
    - Test PDU construction for FC 05, 06, 15, 16
    - Test safe-range rejection with correct error output
    - Test successful write confirmation parsing
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

- [x] 5. Implement Modbus enumeration and fuzzing
  - [x] 5.1 Implement Unit ID enumeration in `src/lib.rs`
    - Implement `enumerate_units(client, timeout_ms) -> Result<ModbusEnumerateResult>`
    - Scan unit IDs 1–247 with FC 03 read probe (address 0, quantity 1)
    - Handle non-responding units (timeout → skip, continue)
    - Record responding_units, total_scanned, elapsed_ms
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 5.2 Implement Modbus fuzzer in `src/fuzz.rs`
    - Use `Xoshiro256PlusPlus` PRNG seeded from config
    - Generate random function codes in range 1–127
    - Generate random payload sizes appropriate per function code
    - Record per-iteration: function_code, payload_size_bytes, responded (bool)
    - Output `ModbusFuzzSummary` with seed, unit_id, iterations_completed, elapsed_ms, records
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 5.3 Write property tests for Modbus fuzzer
    - **Property 7: Modbus Fuzzer Determinism**
    - **Property 8: Modbus Fuzzer Function Code Range**
    - **Validates: Requirements 4.1, 4.4**

- [x] 6. Implement Modbus CLI entry point
  - [x] 6.1 Implement `src/main.rs` for athena-modbus
    - Use `clap::Parser` with long-form flags: `--target`, `--action`, `--unit-id`, `--address`, `--quantity`, `--value`, `--values`, `--seed`, `--iterations`, `--timeout-ms`, `--safe-range-min`, `--safe-range-max`
    - Route to appropriate function based on `--action`
    - Validation errors → `report_validation_error()` (JSON to stderr, exit 1)
    - Successful results → JSON to stdout
    - Include `#[tokio::main]` async entry
    - _Requirements: 12.1, 12.3, 12.5, 12.6, 13.1_

  - [ ]* 6.2 Write unit tests for Modbus CLI argument validation
    - Test valid argument combinations for each action
    - Test missing required args produce validation_error
    - Test out-of-range values (unit_id 0, address > 65535, etc.)
    - _Requirements: 12.1, 12.5_

- [x] 7. Checkpoint — Modbus module complete
  - Ensure all Modbus tests pass (`cargo test -p athena-modbus`)
  - Ensure `cargo build -p athena-modbus` produces binary
  - Ask the user if questions arise.

- [x] 8. Implement CAN frame crafting and validation
  - [x] 8.1 Create `crates/athena-canbus/` crate with Cargo.toml
    - Add workspace member in root `Cargo.toml`
    - Dependencies: `athena-common`, `tokio`, `clap`, `serde`, `serde_json`, `rand`, `rand_xoshiro`, `libc`
    - Dev-dependencies: `proptest`, `tokio-test`
    - _Requirements: 12.7_

  - [x] 8.2 Implement CAN frame validation and crafting in `src/lib.rs`
    - Implement `validate_can_id(id: u32, extended: bool) -> Result<(), String>`
    - Standard: 0–0x7FF; Extended: 0–0x1FFFFFFF
    - Implement `validate_data(data_hex: &str) -> Result<Vec<u8>, String>` (even length, hex chars, max 8 bytes)
    - Implement `craft_frame(id, extended, data_hex) -> Result<CanCraftResult>`
    - Normalize data_hex to lowercase in output
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 8.3 Write property tests for CAN frame validation
    - **Property 4: CAN Frame Validation Correctness**
    - **Property 5: Extended CAN Frame ID Range**
    - **Property 10: Payload Hex Normalization Consistency**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 12.4**

- [x] 9. Implement CAN SocketCAN operations
  - [x] 9.1 Implement SocketCAN raw socket wrapper in `src/socket.rs`
    - Implement `CanSocket::open(interface: &str) -> Result<Self>`
    - Use `libc::socket(AF_CAN, SOCK_RAW, CAN_RAW)`
    - Implement `bind` to interface by index (`libc::if_nametoindex`)
    - Implement `send_frame(&self, frame: &CanFrame) -> Result<()>`
    - Implement `recv_frame(&self, timeout_ms: u64) -> Result<Option<CanFrame>>`
    - Handle interface-not-found → `interface_error`
    - _Requirements: 6.1, 6.4_

  - [x] 9.2 Implement CAN sniff in `src/sniff.rs`
    - Implement `sniff(socket, duration_ms) -> Result<CanSniffResult>`
    - Read frames in a loop until duration elapses
    - Record timestamp_us for each frame (relative to sniff start)
    - Return CanSniffResult with interface, duration_ms, frames vector
    - _Requirements: 6.3, 13.4, 13.5_

  - [x] 9.3 Implement CAN replay in `src/replay.rs`
    - Implement `replay(socket, capture_file_path) -> Result<CanInjectResult>`
    - Read JSON capture file (array of CanSniffFrame objects)
    - Transmit frames with original timing deltas (tokio::time::sleep between frames)
    - Return frame_count and elapsed_ms
    - Handle missing/malformed capture file → `capture_file_error`
    - _Requirements: 7.1_

  - [x] 9.4 Implement CAN injection in `src/lib.rs`
    - Implement `inject_frame(socket, id, extended, data_hex) -> Result<CanInjectResult>`
    - Validate frame, write to socket, return confirmation
    - _Requirements: 6.1_

- [x] 10. Implement CAN fuzzer
  - [x] 10.1 Implement CAN fuzzer in `src/fuzz.rs`
    - Use `Xoshiro256PlusPlus` PRNG seeded from config
    - Generate random IDs within configurable range (default: full standard range 0–0x7FF)
    - Generate random data (0–8 bytes)
    - Transmit each frame via socket
    - Output `CanFuzzSummary` with seed, interface, iterations_completed, id_range, elapsed_ms, frame_count
    - _Requirements: 7.2, 7.3_

  - [ ]* 10.2 Write property test for CAN fuzzer determinism
    - **Property 9: CAN Fuzzer Determinism**
    - Generate frames without socket (mock/collect), verify identical sequences for same seed
    - **Validates: Requirements 7.2**

- [x] 11. Implement CAN CLI entry point
  - [x] 11.1 Implement `src/main.rs` for athena-canbus
    - Use `clap::Parser` with long-form flags: `--interface`, `--action`, `--id`, `--data`, `--extended`, `--duration-ms`, `--capture-file`, `--seed`, `--iterations`, `--id-range-start`, `--id-range-end`, `--timeout-ms`
    - Route to appropriate function based on `--action` (craft, inject, sniff, replay, fuzz)
    - Validation errors → `report_validation_error()` (JSON to stderr, exit 1)
    - Successful results → JSON to stdout
    - _Requirements: 12.2, 12.4, 12.5, 12.7, 13.4_

  - [ ]* 11.2 Write unit tests for CAN CLI argument validation
    - Test valid argument combinations for each action
    - Test missing required args produce validation_error
    - Test invalid hex data, out-of-range IDs
    - _Requirements: 12.2, 12.5_

- [x] 12. Checkpoint — CAN module complete
  - Ensure all CAN tests pass (`cargo test -p athena-canbus`)
  - Ensure `cargo build -p athena-canbus` produces binary
  - Ask the user if questions arise.

- [x] 13. Implement ICS safety controls in the orchestrator
  - [x] 13.1 Create `orchestrator/ics_safety.py`
    - Implement `SafeRange` dataclass (register_address, min_value, max_value)
    - Implement `IcsTargetConfig` dataclass (target_id, host, port, protocol, ics_rate_limit, safe_ranges, capabilities_required)
    - Implement `load_ics_target_config(path: Path) -> IcsTargetConfig` (parse TOML)
    - Implement `validate_write_against_safe_range(address, value, safe_ranges) -> tuple[bool, str | None]`
    - Implement `IcsConfigError` exception class
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.4_

  - [ ]* 13.2 Write property tests for ICS safety controls (hypothesis)
    - **Property 6 (Python port): Safe Range Boundary Enforcement**
    - **Property 11: ICS Rate Limiter Respects Configured Limit**
    - Generate random safe-range configs and values, verify accept/reject
    - Generate random rate limits, verify burst behavior
    - **Validates: Requirements 9.1, 9.2, 9.4, 9.5**

  - [x] 13.3 Integrate ICS safety into orchestrator OPAR loop
    - Extend `agent.py` act phase: detect ICS protocol targets
    - Apply ICS-specific rate limit (from target config) instead of default 60
    - Check `ICS_WRITE` / `CAN_INJECT` capabilities before execution
    - Validate write values against safe_ranges before tool invocation
    - Emit `needs_review` ground-truth record on capability or boundary violation
    - _Requirements: 2.5, 6.2, 7.4, 9.1, 9.3_

- [x] 14. Update tool registry with ICS entries
  - [x] 14.1 Add Modbus and CAN tool entries to `config/tool-registry.toml`
    - Add `modbus-read`, `modbus-write`, `modbus-fuzz`, `modbus-enumerate` entries
    - Add `canbus-craft`, `canbus-inject`, `canbus-sniff`, `canbus-fuzz` entries
    - Define argument schemas with proper type constraints and enums
    - Declare required capabilities: `ICS_WRITE` for modbus-write/fuzz, `CAN_INJECT` for canbus-inject/fuzz
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 14.2 Write property test for tool registry argument validation
    - **Property 12: Tool Registry Argument Validation Bounds**
    - Generate boundary values for Modbus addresses, unit IDs, function codes, CAN IDs
    - Verify validation accepts in-range and rejects out-of-range
    - **Validates: Requirements 8.3**

- [x] 15. Add ICS target configuration files
  - [x] 15.1 Create target configuration files
    - Create `config/targets/openplc.toml` with register maps and safe ranges
    - Create `config/targets/grfics.toml` with process simulator metadata
    - Create `config/targets/vcan-lab.toml` with vcan interface and ID ranges
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ]* 15.2 Write unit tests for target config loading
    - Test loading each config file successfully
    - Test invalid TOML produces IcsConfigError
    - Test missing required fields are caught
    - _Requirements: 10.4_

- [x] 16. Implement ICS eval metrics
  - [x] 16.1 Create `eval/ics_metrics.py`
    - Implement `BoundaryViolation` dataclass
    - Implement `IcsCoverageReport` dataclass
    - Implement `compute_function_code_coverage(records, tested_codes) -> float`
    - Implement `compute_register_coverage(records, address_space_size) -> float`
    - Implement `compute_can_id_coverage(records, id_range) -> float`
    - Implement `compute_safety_compliance(total_writes, boundary_violations) -> float`
    - Implement `generate_ics_report(ground_truth_records, target_config) -> IcsCoverageReport`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 16.2 Write unit tests for ICS eval metrics
    - Test coverage calculations with known data
    - Test boundary violation recording
    - Test zero-division handling (no writes → 100% compliance)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 17. Final checkpoint — Full integration
  - Ensure `cargo test --workspace` passes all Rust tests
  - Ensure `pytest tests/python/ tests/integration/` passes all Python tests
  - Verify tool registry loads without errors
  - Verify target configs parse correctly
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (proptest in Rust, hypothesis in Python)
- Unit tests validate specific examples and edge cases
- The Modbus module and CAN module can be developed in parallel after task 1 is complete
- Integration tests against OpenPLC/vcan require environment setup beyond this implementation plan

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1", "8.1"] },
    { "id": 2, "tasks": ["2.2", "8.2"] },
    { "id": 3, "tasks": ["2.3", "3.1", "8.3", "9.1"] },
    { "id": 4, "tasks": ["3.2", "4.1", "9.2", "9.3", "9.4"] },
    { "id": 5, "tasks": ["3.3", "4.2", "4.3", "5.1", "10.1"] },
    { "id": 6, "tasks": ["4.4", "5.2", "5.3", "6.1", "10.2", "11.1"] },
    { "id": 7, "tasks": ["6.2", "9.1", "11.2"] },
    { "id": 8, "tasks": ["13.1", "14.1", "15.1", "16.1"] },
    { "id": 9, "tasks": ["13.2", "13.3", "14.2", "15.2", "16.2"] }
  ]
}
```
