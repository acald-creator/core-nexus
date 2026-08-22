# 100 Days of Underground Nexus

A hybrid build + use challenge: implement the platform AND use it for real security operations.

**Start date:** 2026-08-18
**End date:** 2026-11-25

## Tracking

| Metric | Target | Current |
|--------|--------|---------|
| Skills generated | 30+ | 14 |
| Detection coverage (% agent actions caught) | 80%+ | — |
| Token efficiency (tokens/scenario trend) | Decreasing | — |
| MITRE ATT&CK techniques exercised | 20+ | — |
| Ground-truth records emitted | 1000+ | 7 |
| Approval queue decisions | 50+ | — |
| Agent sessions completed | 100+ | 1 |

## Daily Template

```
Day X/100 — #100DaysOfNexus

🎯 Today: [one-liner]
🔧 Built: [feature or tool]
🔍 Learned: [key insight]
📊 Metric: [tokens saved / alerts detected / coverage %]

Skills generated: X | Agent sessions: Y
```

---

## Phase 1: Foundation (Days 1-20) — "Make It Run"

- [x] **Day 1** (B) — Implement athena-agent-runtime-wiring: Dockerfile rust-builder stage
- [x] **Day 2** (B) — Implement python-builder stage + integrate into athena-core
- [x] **Day 3** (B) — Create entrypoint script + `orchestrator/__main__.py`
- [x] **Day 4** (U) — First OPAR agent run against Juice Shop — watch it work
- [x] **Day 5** (D) — Document what happened, generate first agent skill from the run
- [x] **Day 6** (B) — Wire Console live badges (alerts count, approvals count from Gateway)
- [x] **Day 7** (B) — Add CORS handling fixes, test Console → Gateway → MinIO flow end-to-end
- [ ] **Day 8** (B) — Add Settings page to Console (config display, token info, service status)
- [ ] **Day 9** (U) — Use Console to monitor a live Athena agent session
- [ ] **Day 10** (D) — Share: "Day 10 — My SOC console watching an AI agent hack"
- [ ] **Day 11** (B) — Implement alerts route in Gateway (pull from Wazuh API)
- [ ] **Day 12** (B) — Implement approvals route in Gateway (pull from athena-agents)
- [ ] **Day 13** (B) — Implement SSE agent events route (stream from athena-agents)
- [ ] **Day 14** (U) — Start SOC baseline stack, generate Athena traffic, triage first real alerts
- [ ] **Day 15** (U) — Correlate Console alerts with nexus-tui feed for the same session
- [ ] **Day 16** (D) — Write a Suricata rule for something Athena generated
- [ ] **Day 17** (B) — Wire nexus-tui to live agent log (fsnotify file watching)
- [ ] **Day 18** (B) — Add WebSocket alternative to SSE for agent events (optional)
- [ ] **Day 19** (U) — Run agent + monitor from terminal only (air-gapped simulation)
- [ ] **Day 20** (D) — Phase 1 retrospective — update ROADMAP, share progress

## Phase 2: Detection Engineering (Days 21-40) — "Catch the Agent"

- [ ] **Day 21** (U) — Run SQLi scenarios against Juice Shop, observe Suricata alerts
- [ ] **Day 22** (U) — Write 3 custom Suricata rules to detect Athena SQLi patterns
- [ ] **Day 23** (B) — Add new Athena tool: directory brute-force (gobuster/ffuf wrapper)
- [ ] **Day 24** (U) — Run the new tool, verify Suricata catches the brute-force traffic
- [ ] **Day 25** (U) — Tune Suricata rules to reduce false positives from labeled traffic
- [ ] **Day 26** (D) — Write detection skill: "How to detect Athena SQLi and brute-force"
- [ ] **Day 27** (B) — Add OpenPLC container to dev compose as a live Modbus target
- [ ] **Day 28** (B) — Wire OpenPLC to Suricata monitoring (mirror traffic)
- [ ] **Day 29** (U) — Run Modbus agent against OpenPLC, watch safe-range enforcement
- [ ] **Day 30** (U) — Attempt boundary violation, verify agent halts and emits needs_review
- [ ] **Day 31** (D) — Share: "Day 31 — AI agent tried to write outside safe range, got blocked"
- [ ] **Day 32** (B) — Implement Wazuh alert transformation in Gateway (map to SOCAlert schema)
- [ ] **Day 33** (B) — Add alert acknowledgment endpoint to Gateway
- [ ] **Day 34** (B) — Wire Console alerts badge to live unacknowledged count
- [ ] **Day 35** (U) — Run a full session: agent generates traffic → alerts appear in Console
- [ ] **Day 36** (U) — Correlate agent ground-truth with Wazuh alerts (true positive rate)
- [ ] **Day 37** (D) — Calculate detection coverage metric, add to tracking table
- [ ] **Day 38** (B) — Add coverage metrics panel to Console or nexus-tui
- [ ] **Day 39** (B) — Add detection coverage to eval/ics_metrics.py in athena-agents
- [ ] **Day 40** (D) — Phase 2 retrospective — detection engineering learnings

## Phase 3: Agent Intelligence (Days 41-60) — "Make It Smarter"

- [ ] **Day 41** (B) — Add multi-step chain support to OPAR planning (sequence objectives)
- [ ] **Day 42** (B) — Add chain state tracking (what's been achieved, what's next)
- [ ] **Day 43** (B) — Add technique selection based on prior observations
- [ ] **Day 44** (U) — Run a 5-step attack chain (recon → exploit → escalate → exfil → cover)
- [ ] **Day 45** (U) — Review ground-truth records for the multi-step chain
- [ ] **Day 46** (D) — Write skill: "Multi-step attack chain planning patterns"
- [ ] **Day 47** (B) — Implement skill loading in OPAR Plan phase (read from MinIO at startup)
- [ ] **Day 48** (B) — Add skill relevance matching (filename/tag based)
- [ ] **Day 49** (B) — Add skill injection into LLM prompt context
- [ ] **Day 50** (U) — Run same scenario twice — with and without loaded skill, compare tokens
- [ ] **Day 51** (D) — Share: "Day 51 — Agent used a learned skill, saved X% tokens"
- [ ] **Day 52** (B) — Add second LLM backend option (vLLM or llama.cpp for comparison)
- [ ] **Day 53** (B) — Add model switching via config (swap without container rebuild)
- [ ] **Day 54** (B) — Add planning quality metrics (actions to objective, dead ends)
- [ ] **Day 55** (U) — Run same scenario with 8B vs 70B model, compare effectiveness
- [ ] **Day 56** (U) — Measure: actions to objective, token cost, planning quality
- [ ] **Day 57** (D) — Write comparison: "LLM model size vs agent effectiveness"
- [ ] **Day 58** (B) — Implement approval write-back in nexus-tui (approve → file/API)
- [ ] **Day 59** (B) — Implement approval write-back in Console (approve → Gateway → agents)
- [ ] **Day 60** (D) — Phase 3 retrospective — agent intelligence findings

## Phase 4: Hardening & Integration (Days 61-80) — "Make It Solid"

- [ ] **Day 61** (B) — Deploy agent to real k3d cluster with agent overlay
- [ ] **Day 62** (B) — Verify NetworkPolicy blocks unauthorized egress (test escape attempts)
- [ ] **Day 63** (B) — Add resource limits and OOM handling for long-running scenarios
- [ ] **Day 64** (U) — Run agent in k8s, verify isolation and capability enforcement
- [ ] **Day 65** (D) — Document k8s agent deployment runbook
- [ ] **Day 66** (B) — Add SBOM generation to local build (syft integration)
- [ ] **Day 67** (B) — Add cosign signing to local build workflow
- [ ] **Day 68** (B) — Add image verification step to run-athena-profile.sh
- [ ] **Day 69** (U) — Build, sign, verify, run — full supply chain loop locally
- [ ] **Day 70** (U) — Attempt to run an unsigned/tampered image — verify rejection
- [ ] **Day 71** (D) — Share: "Supply chain security for an AI offensive agent"
- [ ] **Day 72** (B) — Add ChromaDB container to dev compose for vector memory
- [ ] **Day 73** (B) — Implement embedding pipeline (skill files → vectors)
- [ ] **Day 74** (B) — Implement RAG query in OPAR Plan phase
- [ ] **Day 75** (U) — Test: "What did I do last time with Modbus?" → retrieves relevant skill
- [ ] **Day 76** (U) — Compare skill retrieval: filename match vs semantic search
- [ ] **Day 77** (D) — Write skill: "Setting up vector memory for agent RAG"
- [ ] **Day 78** (B) — Add session log embedding (episodic memory → vector store)
- [ ] **Day 79** (B) — Add "similar past sessions" context to OPAR planning
- [ ] **Day 80** (D) — Phase 4 retrospective — platform hardening complete

## Phase 5: Advanced Scenarios (Days 81-100) — "Push the Limits"

- [ ] **Day 81** (B) — Add vcan interface setup to dev compose (virtual CAN Bus lab)
- [ ] **Day 82** (B) — Wire CAN tools to compose profile (athena-agent-ics)
- [ ] **Day 83** (B) — Create CAN Bus target config with ID ranges and fuzz params
- [ ] **Day 84** (U) — Run CAN fuzzer agent, observe frame generation
- [ ] **Day 85** (U) — Analyze CAN fuzzer output — coverage of ID space
- [ ] **Day 86** (D) — Document ICS/OT agent safety controls in action
- [ ] **Day 87** (B) — Implement multi-agent: two OPAR loops, shared observation store
- [ ] **Day 88** (B) — Add coordination protocol (agent A informs agent B of findings)
- [ ] **Day 89** (B) — Add conflict detection (don't scan same target simultaneously)
- [ ] **Day 90** (U) — Run two agents against different targets, watch coverage expand
- [ ] **Day 91** (U) — Measure: combined coverage vs single agent, coordination overhead
- [ ] **Day 92** (D) — Share: "Multi-agent adversary emulation — lessons learned"
- [ ] **Day 93** (B) — Build scoring engine (automated effectiveness measurement)
- [ ] **Day 94** (B) — Define challenge scenarios with objective criteria
- [ ] **Day 95** (B) — Implement leaderboard (track agent performance across runs)
- [ ] **Day 96** (U) — Run scored challenge: "Compromise Juice Shop in fewest actions"
- [ ] **Day 97** (U) — Run scored challenge: "Map all Modbus registers without triggering alert"
- [ ] **Day 98** (D) — Final retrospective — what worked, what didn't, what's next
- [ ] **Day 99** (B) — Polish all docs, READMEs, architecture for public consumption
- [ ] **Day 100** (D) — Final share: "100 Days of Underground Nexus — Complete"

---

## Progress Log

### Phase 1

| Day | Date | Type | Summary | Skill Generated |
|-----|------|------|---------|-----------------|
| 1 | 2026-08-18 | B | rust-builder / runtime wiring in nexus-athena + athena-agents | |
| 2 | 2026-08-19 | B | python-builder, Juice Shop compose target, allowlist | |
| 3 | 2026-08-18 | B | entrypoint + `orchestrator/__main__.py` | |
| 4 | 2026-08-22 | U | First OPAR run vs Juice Shop (`localhost:3001`), 6 actions, `limit-reached` in 30s. Plan used gemma3:12b (nmap → login → http-request). Act phase still stubbed. GT: `/tmp/juice-shop-day4-gt.jsonl` | |
| 5 | 2026-08-22 | D | Documented Juice Shop run. Skill: allowlist host:port identity (first-match bug, host vs compose, stub Act ≠ traffic) | red-team-allowlist-target-identity.md |
| 6 | 2026-08-22 | B | Sidebar badges live from Gateway: unacknowledged critical+high alerts, pending approvals. Property 16. | |
| 7 | 2026-08-22 | B | CORS 204 preflight, Console gateway URL 3100, MinIO public presign rewrite. 5 tests. | code-console-gateway-minio-browser-path.md |

### Phase 2

| Day | Date | Type | Summary | Skill Generated |
|-----|------|------|---------|-----------------|
| | | | | |

### Phase 3

| Day | Date | Type | Summary | Skill Generated |
|-----|------|------|---------|-----------------|
| | | | | |

### Phase 4

| Day | Date | Type | Summary | Skill Generated |
|-----|------|------|---------|-----------------|
| | | | | |

### Phase 5

| Day | Date | Type | Summary | Skill Generated |
|-----|------|------|---------|-----------------|
| | | | | |

---

## Prerequisites (Already Done)

- [x] Kiro auto-skill-gen workflow (hooks + steering + seed skills)
- [x] Architecture docs expanded for LLM agent stimulation/emulation
- [x] nexus-tui expanded (4-panel terminal console)
- [x] Portable agent memory (git skills + MinIO sync)
- [x] Architecture revision (doc 13, component map updated)
- [x] nexus-athena profiles (agent, agent-ics compose + k8s + validation)
- [x] Nexus Console fully implemented (7 panels, dark theme, auth)
- [x] API Gateway scaffold with all routes (FastAPI, port 3100)
- [x] Unified dev compose stack (Console + Gateway + MinIO + AI Inference)
- [x] Agent config directory (tool-registry, allowlist, targets, LLM config)
- [x] athena-agent-runtime-wiring spec (ready for implementation)
