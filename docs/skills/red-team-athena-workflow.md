---
name: Athena Red Team Workflow
description: Structured approach for offensive security tasks in Nexus Athena
tags: [red-team, athena, adversary-emulation]
inclusion: manual
---

## When to Apply
- Working in the nexus-athena repository
- Building or modifying offensive tooling (Modbus, CAN, network reconnaissance)
- Designing adversary emulation scenarios or attack chains
- Evaluating ICS/OT targets with safety constraints

## Approach
1. Identify the target protocol and environment (ICS/OT vs standard network)
2. Check `config/targets/` for existing target configurations and safe ranges
3. Check `config/tool-registry.toml` for available tools and capability requirements
4. Verify capability gates — ICS_WRITE, CAN_INJECT require explicit declaration
5. Implement with safety validation first (safe ranges, rate limits) before offensive logic
6. Use deterministic PRNG (Xoshiro256PlusPlus) with configurable seed for reproducibility
7. Output results as structured JSON (stdout for data, stderr for errors)
8. Run eval metrics after execution to measure coverage and compliance

## Key Patterns
- Rust crates follow `crates/athena-<module>/` layout
- CLI uses clap with long-form flags, JSON output
- Safety validation: `validate_write_value(address, value, safe_ranges)`
- Rate limiting per-target from TOML config (`ics_rate_limit` field)
- Ground truth records: `needs_review` on capability/boundary violations
- Property tests with proptest for correctness invariants
- OPAR loop in orchestrator: Observe → Plan → Act → Report

## Pitfalls
- Never bypass safe-range validation for "testing convenience"
- Don't hardcode credentials or target IPs in source
- Keep offensive tooling isolated from SOC control-plane code
- Don't add broad host Docker access to default examples
- SocketCAN operations require Linux — mock on macOS for unit tests

## References
- `nexus-athena/crates/athena-modbus/` — Modbus TCP module
- `nexus-athena/crates/athena-canbus/` — CAN Bus module
- `nexus-athena/config/tool-registry.toml` — tool definitions
- `nexus-athena/config/targets/` — target TOML configs
- `nexus-athena/orchestrator/ics_safety.py` — Python safety controls
- `nexus-athena/eval/ics_metrics.py` — coverage and compliance metrics
