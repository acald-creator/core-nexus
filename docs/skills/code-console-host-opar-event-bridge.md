---
name: Console Host OPAR Event Bridge
description: Host-side Athena OPAR writes GT JSONL only; Console Agent Feed needs athena-agents HTTP /sessions and /events. Bridge GT→SSE until Day 13 ships a real event API.
tags: [code-debug, nexus-console, athena-agents, sse, opar]
inclusion: manual
---

## When to Apply
- Console Agent Feed is empty or Gateway SSE shows `UPSTREAM_DISCONNECTED`
- `GET /api/v1/agents/sessions` returns 502 while host OPAR is clearly writing GT JSONL
- You are running orchestrator on the host (not inside a compose service that exposes `:8080`)
- Day 9-style: "use Console to monitor a live Athena session" before athena-agents has an HTTP event surface

## Approach
1. Confirm the gap: Gateway proxies agents to `http://127.0.0.1:8080`. Host OPAR does **not** listen there. GT path (`ATHENA_GT_OUTPUT`) is not an event bus.
2. Until Day 13, run a temporary shim that (a) serves `/sessions`, `/events` (SSE), `/approvals` on `:8080`, and (b) tails the GT JSONL and maps records to Console OPAR-shaped events.
3. Point the host planner at a reachable LLM (`OLLAMA_HOST`). If the real registry is unreachable, a canned `/api/generate` mock is enough for a Use-day proof.
4. Prefer tools that exist on the host. `port-scanner` → `${ATHENA_BIN_DIR}/athena-scanner` fails without that binary; `http-request` against an allowlisted Juice Shop works.
5. Do **not** `rm` the GT file while the shim is tailing it — truncate (`: > path`) or reopen on inode change. Otherwise SSE only gets the hello event.
6. Prove the pipe: login → `GET /api/v1/agents/sessions` shows the shim session → subscribe `GET /api/v1/agents/events` → run OPAR → count `data:` lines (hello + GT rows).

## Key Patterns
- Console `useAgentFeed` → Gateway `/api/v1/agents/events` (SSE, default) or `/api/v1/agents/events/ws` (WebSocket)
- WebSocket is optional (Day 18). Same OPAR JSON envelopes. Auth is still `?token=` because browsers cannot set WS headers.
- Set `VITE_AGENT_FEED_TRANSPORT=websocket` (or `agentFeedTransport` in `config.json`) to switch the Console. SSE stays default.
- Bridge script: `scripts/day9-console-bridge.py` (stdlib mock Ollama `:11435` + athena shim `:8080`)
- GT labels map to feed outcomes; `needs_review` → pending, else success for Day 9 visibility
- Day 13 should replace the shim with a real athena-agents event API, not keep the Use-day bridge

## Pitfalls
- A healthy host OPAR log is not evidence the Console can see the session
- Recreating the GT file (`rm` + `touch`) orphans an open tail fd — events never broadcast
- Real Ollama model pulls can fail in restricted networks; do not block the Use-day on gemma if a canned planner proves the feed
- Gateway auth: SSE and WebSocket often need `?token=` because EventSource/WebSocket cannot set Authorization headers
- Do not commit bridge processes or `/tmp` GT files as production architecture

## References
- `scripts/day9-console-bridge.py`
- `platform/api-gateway` agents proxy (`/api/v1/agents/*`)
- `platform/nexus-console` Agent Feed / `useAgentFeed`
- Day 13 brief: implement SSE agent events from athena-agents
