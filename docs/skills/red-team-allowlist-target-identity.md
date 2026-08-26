---
name: Allowlist Target Identity (Host vs Compose)
description: Keep Athena allowlist, target TOML, and planner prompts on the same host:port identity when running OPAR on the host versus inside compose
tags: [red-team, athena, opar, allowlist, docker]
inclusion: manual
---

## When to Apply
- Running the OPAR orchestrator natively on the host against a compose-published target
- Adding a second service that also uses `localhost` to the allowlist
- Debugging "target reachable" on the wrong port
- After a rehearsal target (different app, same hostname) leaves constants in prompts or config

## Approach
1. Decide the execution context first: host process vs `athena.agent` container
2. Pick one identity and use it everywhere (target TOML host/port, allowlist entry, planner base URL)
   - Host run: `localhost` + published port (Juice Shop is `3001`)
   - Compose run: compose hostname + internal port (`juice-shop.lab:3000`)
3. Put both identities in the allowlist if you will run both ways. Do not assume one `localhost` entry covers every local app
4. Confirm reachability with the same host:port the orchestrator will use (`curl -I http://127.0.0.1:3001/` for a host run)
5. Isolate the allowlist to a single entry when debugging a first run, then merge back
6. Regenerate `allowlist.sha256` after any allowlist edit (`shasum -a 256 allowlist.json`)
7. After the run, read ground-truth JSONL and the log line `Target reachable:` before treating the scenario as hitting the intended app

## Key Patterns
- `_get_target_port()` in `orchestrator/agent.py` returns the first allowlist row whose `host` matches. Two `localhost` rows mean the first port wins
- Juice Shop compose: hostname `juice-shop.lab`, container port `3000`, host map `3001:3000`
- Grimoire host: `127.0.0.1:4400` (SvelteKit UI; proxies `/api` to cargo `:3010`). Do not store the operator password in Athena config. Grimoire compose API: `grimoire.lab:3000`
- Planner prompt must use the allowlist port, not a leftover rehearsal port
- Cap `max_actions` (5–8) for a watchable first run; Juice Shop target default is 50
- Ground-truth `label: malicious` plus `scenario_complete` still does not prove the planned technique ran. Read `output.status` (`executed`, `rejected`, `error`) and HTTP `status_code` / subprocess `returncode`

## Pitfalls
- Do not add a second `localhost` allowlist entry and expect the Juice Shop port to be selected
- Do not list Grimoire as `localhost:4400`. `localhost` is already novel-directory `:8090`. Use `127.0.0.1:4400` or `grimoire.lab:3000`
- `host.docker.internal` is for container-to-host. It is the wrong identity for a host-side orchestrator
- A hardcoded base URL port (the `:8090` leftover from novel-directory) will aim Plan at the wrong service even when TCP checks the right one
- Native host traffic never hits Suricata on `athena_lab`. Detection days require the agent container on the same network as the target
- Do not treat ATT&CK IDs in JSONL as ground truth of what executed. Act now invokes registered tools, but invented tool IDs (`login-user`) are rejected and HTTP is GET-only

## References
- `athena-agents/orchestrator/agent.py` — `_get_target_port()`, `plan()` base URL, `act()`
- `athena-agents/orchestrator/executor.py` — subprocess argv, constrained nmap, GET-only `http-request`
- `athena-agents/orchestrator/allowlist.py` — host/port_range matching
- `nexus-athena/config/allowlist.json` + `allowlist.sha256`
- `nexus-athena/config/targets/juice-shop.toml`
- `nexus-athena/config/targets/grimoire.toml` and `grimoire-lab.toml`
- `grimoire-workbench/docker-compose.athena.yml`
- `nexus-athena/deploy/compose/athena-profiles.yml` — juice-shop service
- Day 4 Juice Shop run: `/tmp/juice-shop-day4-gt.jsonl`
