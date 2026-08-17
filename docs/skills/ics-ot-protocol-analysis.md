---
name: ICS/OT Protocol Analysis
description: Analyzing and testing industrial control system protocols (Modbus TCP, CAN Bus, DNP3)
tags: [ics, ot, modbus, canbus, scada, safety]
inclusion: manual
---

## When to Apply
- Analyzing ICS/OT protocol traffic or implementing protocol handlers
- Working with Modbus TCP (function codes, MBAP headers, register maps)
- Working with CAN Bus (frame crafting, SocketCAN, sniffing, replay)
- Evaluating safety boundaries for write operations
- Fuzzing ICS protocol implementations

## Approach
1. Identify the protocol and target environment from config
2. Load target configuration (register maps, safe ranges, rate limits)
3. For reads: no safety gate needed, use appropriate function code
4. For writes: validate against safe ranges BEFORE any network operation
5. For fuzzing: use seeded PRNG, log every iteration, respect rate limits
6. For sniffing: capture with timestamps, output as structured JSON array
7. Compute coverage metrics after any test run
8. Record boundary violations as ground-truth for eval

## Key Patterns
- Modbus MBAP header: transaction_id (u16) + protocol_id (0x0000) + length (u16) + unit_id (u8)
- Function codes: FC01 read coils, FC02 discrete inputs, FC03 holding regs, FC04 input regs, FC05 write coil, FC06 write reg, FC15 write multi coils, FC16 write multi regs
- Exception response: function_code OR 0x80
- CAN standard ID: 0-0x7FF (11-bit), extended: 0-0x1FFFFFFF (29-bit)
- CAN data: max 8 bytes, hex-encoded in config/output
- Safe range format: `{ address, min_value, max_value }`
- Deterministic fuzzing: same seed + same config = same frame sequence

## Pitfalls
- Unit ID 0 is broadcast — scanning should use 1-247
- Modbus TCP has no built-in auth — treat all targets as sensitive
- CAN SocketCAN requires Linux kernel support (AF_CAN)
- Never skip safe-range validation even in "test mode"
- Rate limits are per-target, not global — check target TOML
- Extended CAN frames need EFF flag set in socket frame struct

## References
- Modbus Application Protocol Specification (modbus.org)
- Linux SocketCAN documentation (kernel.org)
- `config/targets/openplc.toml` — Modbus target with register maps
- `config/targets/vcan-lab.toml` — virtual CAN lab config
- `crates/athena-modbus/src/frame.rs` — MBAP encoding/decoding
- `crates/athena-canbus/src/socket.rs` — SocketCAN wrapper
