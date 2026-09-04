# 100 Days of Underground Nexus

A hybrid build + use challenge: implement the platform AND use it for real security operations.

> **Note:** Challenge “Phase 1/2/3” below are **calendar buckets** (day ranges). They are
> **not** the architecture roadmap phases in `docs/architecture/03-phased-implementation-roadmap.md`.

**Start date:** 2026-08-18
**End date:** 2026-11-25

## Tracking

| Metric | Target | Current |
|--------|--------|---------|
| Skills generated | 30+ | 18 |
| Detection coverage (% agent actions caught) | 80%+ | Suricata SIDs hit on labeled SQLi (Day 21); formal % TBD Day 37 |
| Token efficiency (tokens/scenario trend) | Decreasing | — |
| MITRE ATT&CK techniques exercised | 20+ | 2+ (T1595, T1190) |
| Ground-truth records emitted | 1000+ | ~28 (Juice Shop OPAR + Night Quire labeled probes) |
| Approval queue decisions | 50+ | — |
| Agent sessions completed | 100+ | 4 (2 OPAR + 2 labeled-probe Use) |

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
- [x] **Day 8** (B) — Add Settings page to Console (config display, token info, service status)
- [x] **Day 9** (U) — Use Console to monitor a live Athena agent session
- [x] **Day 10** (D) — Share: "Day 10 — My SOC console watching an AI agent hack"
- [x] **Day 11** (B) — Implement alerts route in Gateway (pull from Wazuh API)
- [x] **Day 12** (D) — Catch-up: document current core-nexus platform state (R2, Vault/hashistack, SOC k8s, Gateway/Console)
- [x] **Day 13** (D) — Catch-up: audit 100 Days vs repo — stubs, supersessions, deferred Builds
- [x] **Day 14** (U) — Start SOC baseline stack, generate Athena traffic, triage first real alerts — *Sep 3: hybrid-sensor + labeled Night Quire probe; `scripts/day14-hybrid-soc-use.sh`*
- [x] **Day 15** (U) — Correlate Console alerts with nexus-tui feed for the same session — *Sep 3: `scripts/day15-correlate-session.sh`; 4 act / 1 triage match (0.25)*
- [x] **Day 16** (D) — Write a Suricata rule for something Athena generated — *Sep 3: SIDs 20261601–20261603 (X-Athena header, UA, Juice Shop OR 1=1)*
- [x] **Day 17** (B) — Wire nexus-tui to live agent log (fsnotify file watching)
- [x] **Day 18** (B) — Add WebSocket alternative to SSE for agent events (optional) — *Sep 3: Gateway `/api/v1/agents/events/ws`; Console `VITE_AGENT_FEED_TRANSPORT`*
- [x] **Day 19** (U) — Run agent + monitor from terminal only (air-gapped simulation) — *Sep 3: `scripts/day19-airgap-terminal.sh`; TUI `--dump`; Zarf `nexus-airgap-ops`*
- [x] **Day 20** (D) — Phase 1 retrospective — update ROADMAP, share progress — *Sep 3: architecture roadmap + changelog*

### Deferred Builds (was Days 12–13 B — do before or interleaved with Days 14–20)

- [ ] **Approvals typed Gateway contract** — `ApprovalAction` models, pending-default sort (Property 8), decision 404/409/502 (was Day 12 B) — *partial Sep 1: factory review webhook + merged queue (`ae4477d`); Athena models / Property 8 still open*
- [ ] **athena-agents SSE event API** — real `/sessions` + `/events`; retire Day 9 GT→SSE bridge (was Day 13 B)

## Phase 2: Detection Engineering (Days 21-40) — "Catch the Agent"

- [x] **Day 21** (U) — Run SQLi scenarios against Juice Shop, observe Suricata alerts — *Sep 4: multi-iface capture; :3003 Juice Shop; SIDs 20261601–203 in eve.json*
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
- [x] **Day 32** (B) — Implement Wazuh alert transformation in Gateway (map to SOCAlert schema) — *done early as Day 11; Indexer-vs-Manager hardening can still land later*
- [ ] **Day 33** (B) — Add alert acknowledgment endpoint to Gateway
- [ ] **Day 34** (B) — Wire Console alerts badge to live unacknowledged count — *partial via Day 6; needs Day 33 ack API to be meaningful*
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
| 8 | 2026-08-23 | B | Settings page: config, JWT claims (no raw token), service health table. Property 17. | |
| 9 | 2026-08-26 | U | Console Agent Feed via Day9 GT→SSE bridge; Juice Shop 6 http-request acts; 8 SSE events | code-console-host-opar-event-bridge.md |
| 10 | 2026-08-27 | D | Share writeup: SOC console watching Athena vs Juice Shop; honest gap + bridge narrative | |
| 11 | 2026-08-28 | B | Gateway alerts: SOCAlert map, filters, triage 404/504; Properties 5–7 | |
| 12 | 2026-08-29 | D | Catch-up: platform state — R2 overlay, hashistack Vault, SOC k8s Gateway/Console/Wazuh, Day 9 bridge gated | |
| 13 | 2026-08-30 | D | Catch-up: full repo audit vs 100 Days; approvals+SSE Builds deferred; architecture overclaim note | |
| 14 | 2026-08-31 | B | *(prep)* ai-inference triage persistence, Gateway contract, k8s thin-lab overlay | |
| 14 | 2026-09-03 | U | Hybrid-sensor Use: labeled Night Quire probes → triage; gateway alerts_source=triage | |
| 15 | 2026-09-01 | D | Changelog Days 12–14 published to acaldwell.dev | |
| 15 | 2026-09-03 | U | GT ↔ triage correlation export for nexus-tui (4 act / 1 alert, ratio 0.25) | |
| 16 | 2026-09-02 | B | Factory review webhook + merged Approvals queue (ADR 0009 F2) | |
| 16 | 2026-09-03 | D | Custom Suricata athena.rules SIDs 20261601–20261603; HTTP_PORTS includes lab 8090/3001 | |
| 17 | 2026-09-03 | B | nexus-tui Agent Feed now live tails OPAR JSONL via fsnotify; auto-updates on log append (manual `r` reload still works) | |
| 18 | 2026-09-03 | B | Gateway WebSocket `/api/v1/agents/events/ws`; Console optional `VITE_AGENT_FEED_TRANSPORT=websocket` (SSE default) | code-gateway-agent-event-websocket.md |
| 19 | 2026-09-03 | U | Terminal-only Night Quire probes + nexus-tui --dump (no Console); Zarf nexus-airgap-ops package created | ops-airgap-terminal-tui.md |
| 20 | 2026-09-03 | D | Phase 1 retrospective: calendar Days 1–20 closed; roadmap exit note; Phase 2 detection focus | |
| 21 | 2026-09-04 | U | Juice Shop SQLi via vznat path; Suricata multi-iface; SIDs 20261601–203 in eve.json | blue-team-suricata-multi-iface-capture.md |
| 32 | 2026-08-28 | B | *(early)* SOCAlert transform — same ship as Day 11; left numbered here for Phase 2 continuity | |

### Parallel platform work (Aug 28–31) — folded into Days 12–14 docs

Does **not** complete Use-days 14+ or the deferred Approvals/SSE Builds:

- **Object store:** R2 overlay for non-lab; MinIO remains lab default (Day 7 path still valid)
- **Secrets:** Vault owned by `nexus-hashistack`; gateway AppRole hydrate; Console lab bypass / local-user allowlist
- **SOC k8s:** Gateway + Console Deployments, Wazuh Vault-synced secrets, indexer TLS, Jupyter + Athena range overlay; webtop-soc remote retired from k8s base
- **Day 9 bridge:** still present, gated in compose — real athena-agents SSE still deferred
- **Approvals:** route scaffold only (no typed models / Property 8)
- **Metadata:** D1 artifact index Worker + gateway client (adjacent to artifacts, not a challenge day)
- **AI inference:** SQLite triage store, Gateway camelCase mapping, k8s overlay + Flux pin (`6077cbd`, `ece62c7`)
- **Hybrid sensor Use (Sep 3):** `scripts/day14-hybrid-soc-use.sh`, `scripts/day15-correlate-session.sh`, `scripts/labeled-probe-session.py`
- **Factory ADR 0009:** `nebucloud/factory-agents` locked for secure coding/review agents; F2 gateway webhook + merged Approvals (`ae4477d`)
- **ADR 0010 (proposed):** shared LLM serving plane with kvcached — not deployed

### Phase 2

| Day | Date | Type | Summary | Skill Generated |
|-----|------|------|---------|-----------------|
| 32 | 2026-08-28 | B | See Phase 1 note — checked early via Day 11 | |

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
