---
name: Gateway Agent Event WebSocket
description: Optional WebSocket alternative to SSE for Console Agent Feed OPAR events
tags: [code-debug, nexus-console, api-gateway, websocket, sse]
inclusion: manual
---

## When to Apply
- Adding or debugging `/api/v1/agents/events/ws`
- Console Agent Feed should use WebSocket instead of EventSource
- A client cannot use SSE (some proxies, bidirectional later)

## Approach
1. Keep SSE as the default. WebSocket is an **alternative**, not a replacement.
2. Gateway: authenticate inside the WebSocket handler — `JWTAuthMiddleware` is HTTP-only.
3. Envelope parity: `{ event: "opar"|"error"|"heartbeat", id?, data }` matching SSE event names.
4. Heartbeat as JSON frames (browsers do not expose WS ping).
5. Console: `VITE_AGENT_FEED_TRANSPORT=websocket` or `config.json` `agentFeedTransport`.
6. Reconnect with exponential backoff in the client; Gateway also retries upstream.

## Key Patterns
- Route: `platform/api-gateway/src/routes/agents.py` — `@router.websocket("/events/ws")`
- Hook: `useAgentFeed` + `toGatewayWebSocketUrl`
- Tests: `platform/api-gateway/tests/test_agent_events_ws.py`

## Pitfalls
- Closing the socket on unmount must not schedule another reconnect (null the ref before `close()`)
- `?token=` still leaks in access logs like SSE — same lab tradeoff
- This does **not** retire the Day 9 GT→SSE bridge; athena-agents still needs `/sessions`+`/events`

## References
- `.kiro/specs/nexus-api-gateway/requirements.md` Requirement 5b
- `docs/skills/code-console-host-opar-event-bridge.md`
