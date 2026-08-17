---
name: Log and Code Bug Analysis
description: Systematic approach to analyzing logs and debugging code issues across the Nexus platform
tags: [debugging, log-analysis, code-review, troubleshooting]
inclusion: manual
---

## When to Apply
- Analyzing application or system logs for anomalies
- Debugging failing builds, tests, or runtime errors
- Investigating container health issues in compose stacks
- Tracing execution paths through multi-crate Rust workspaces or Python orchestrators
- Post-mortem analysis of incidents

## Approach
1. Collect context: error message, stack trace, log timestamps, affected service
2. Identify the layer: infrastructure (Docker/compose), application (Rust/Python), protocol (Modbus/CAN)
3. Check recent changes: `git log --oneline -10` in the relevant repo
4. For Rust: check `cargo build` output, look for type mismatches, lifetime errors, missing imports
5. For Python: check traceback, verify imports, check type annotations vs runtime values
6. For containers: check `docker logs <service>`, healthcheck status, volume mounts
7. Isolate: can you reproduce with a minimal case or unit test?
8. Fix and verify: make the change, run the specific test, then broader suite
9. Document the root cause and fix pattern for future reference

## Key Patterns
- Rust common issues: missing `use` imports, trait not in scope, lifetime annotations needed for async
- Python common issues: circular imports in orchestrator, missing `__init__.py`, type errors at runtime
- Container issues: healthcheck timing (increase TIMEOUT_SECONDS), cert path mismatches, volume permissions
- Compose issues: service dependency ordering, network isolation between stacks
- Log patterns: look for timestamps clustering, repeated errors (crash loop), state transitions

## Pitfalls
- Don't chase symptoms — trace to root cause before fixing
- Don't assume the first error in a log is the root cause (check earlier warnings)
- Rust: don't fight the borrow checker with unsafe — restructure ownership instead
- Containers: don't rebuild the whole image for a config change (use volume mounts for dev)
- Always verify the fix doesn't break adjacent functionality (run full test suite)

## References
- `scripts/validate-analyst-image.sh` — container health verification
- `cargo test --workspace` — full Rust test suite
- `pytest tests/` — Python test suite
- `docker compose -f <stack> logs <service>` — service log inspection
- Tetragon scenario logs in core-nexus root — runtime security telemetry examples
