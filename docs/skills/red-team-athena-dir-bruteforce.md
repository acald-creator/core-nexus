---
name: Athena Directory Brute-Force Tool
description: Add or extend the gobuster-style dir-bruteforce Athena tool (in-process, labeled, clamped)
tags: [red-team, athena, directory-bruteforce, detection]
inclusion: manual
---

## When to Apply
- Adding or changing Athena directory discovery (Day 23+)
- Preparing Day 24 Suricata verification of brute-force traffic
- Preferring labeled GETs over shelling out to gobuster/ffuf

## Approach
1. Implement in **`athena-agents`** (`orchestrator/tools/dir_bruteforce.py`), not core-nexus.
2. Register `[tools.dir-bruteforce]` in **both** `athena-agents/config/tool-registry.toml` and `nexus-athena/config/tool-registry.toml`.
3. Wire `execute_tool` for `dir-bruteforce` (allowlist gate + Athena headers).
4. Clamp wordlist (≤64), concurrency (≤8); sanitize path tokens; no free-form flags.
5. Optional wordlist file: `config/wordlists/common-dirs.txt` (synced to nexus-athena).
6. Explicit `words` argument replaces the built-in list (tests / tiny lab runs).

## Key Patterns
- In-process httpx GETs so `X-Athena-*` labels reach Suricata (Day 21/22 capture path).
- Hits = status in {200,201,204,301,302,307,308,401,403}.
- `wrapper: in-process-gobuster-style` in tool output — honest about not invoking the binary.

## Pitfalls
- Subprocess gobuster without header injection → unlabeled traffic, harder Day 24.
- Host-native probes may miss Suricata (use in-cluster → `host.docker.internal`).
- Do not put offensive tool code under `core-nexus/platform/athena/`.

## References
- `athena-agents/orchestrator/tools/dir_bruteforce.py`
- `athena-agents/orchestrator/executor.py`
- `docs/skills/blue-team-athena-suricata-http-labels.md`
