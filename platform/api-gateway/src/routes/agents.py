"""Agent routes — sessions and SSE event streaming."""
import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

HEARTBEAT_INTERVAL = 15
RECONNECT_BASE_DELAY = 1
RECONNECT_MAX_DELAY = 30


@router.get("/sessions")
async def list_agent_sessions(request: Request):
    """List current and recent agent sessions."""
    try:
        sessions = await request.app.state.athena_client.get_sessions()
        return sessions
    except Exception:
        raise HTTPException(status_code=502, detail="athena-agents service unavailable")


async def _event_generator(request: Request):
    """Generator that yields OPAR events with heartbeat and reconnection."""
    athena_client = request.app.state.athena_client
    reconnect_delay = RECONNECT_BASE_DELAY

    while True:
        try:
            async for event in athena_client.get_event_stream():
                reconnect_delay = RECONNECT_BASE_DELAY
                yield {
                    "event": "opar",
                    "data": json.dumps(event),
                    "id": event.get("id", ""),
                }
        except asyncio.CancelledError:
            break
        except Exception:
            yield {
                "event": "error",
                "data": json.dumps({"error": "Upstream connection lost", "code": "UPSTREAM_DISCONNECTED"}),
            }
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, RECONNECT_MAX_DELAY)


@router.get("/events")
async def agent_event_stream(request: Request):
    """SSE stream of OPAR events from athena-agents."""
    return EventSourceResponse(
        _event_generator(request),
        ping=HEARTBEAT_INTERVAL,
    )
