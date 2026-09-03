"""Agent routes — sessions, SSE, and WebSocket event streaming."""
import asyncio
import json

import jwt
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from sse_starlette.sse import EventSourceResponse
from starlette.websockets import WebSocketState

router = APIRouter()

HEARTBEAT_INTERVAL = 15
RECONNECT_BASE_DELAY = 1
RECONNECT_MAX_DELAY = 30
WS_CLOSE_UNAUTHORIZED = 4401


def _opar_envelope(event: dict) -> dict:
    return {
        "event": "opar",
        "data": event,
        "id": event.get("id", ""),
    }


def _upstream_error_envelope() -> dict:
    return {
        "event": "error",
        "data": {"error": "Upstream connection lost", "code": "UPSTREAM_DISCONNECTED"},
    }


def _token_from_websocket(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return websocket.query_params.get("token")


def _decode_agent_token(token: str, jwt_secret: str, algorithm: str) -> None:
    jwt.decode(token, jwt_secret, algorithms=[algorithm])


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
                env = _opar_envelope(event)
                yield {
                    "event": env["event"],
                    "data": json.dumps(env["data"]),
                    "id": env["id"],
                }
        except asyncio.CancelledError:
            break
        except Exception:
            err = _upstream_error_envelope()
            yield {
                "event": err["event"],
                "data": json.dumps(err["data"]),
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


async def _accept_authorized_websocket(websocket: WebSocket) -> bool:
    """JWT on the socket itself — HTTP auth middleware does not cover WebSocket."""
    settings = websocket.app.state.settings
    token = _token_from_websocket(websocket)
    if not token:
        if websocket.client_state == WebSocketState.CONNECTING:
            await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return False
    try:
        _decode_agent_token(token, settings.jwt_secret, settings.jwt_algorithm)
    except jwt.ExpiredSignatureError:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return False
    except jwt.InvalidTokenError:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return False
    await websocket.accept()
    return True


async def _websocket_event_loop(websocket: WebSocket) -> None:
    athena_client = websocket.app.state.athena_client
    reconnect_delay = RECONNECT_BASE_DELAY

    while True:
        try:
            stream = athena_client.get_event_stream()
            agen = stream.__aiter__()
            while True:
                try:
                    event = await asyncio.wait_for(agen.__anext__(), timeout=HEARTBEAT_INTERVAL)
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    await websocket.send_json({"event": "heartbeat"})
                    continue
                reconnect_delay = RECONNECT_BASE_DELAY
                await websocket.send_json(_opar_envelope(event))
        except WebSocketDisconnect:
            break
        except asyncio.CancelledError:
            break
        except Exception:
            try:
                await websocket.send_json(_upstream_error_envelope())
            except Exception:
                break
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, RECONNECT_MAX_DELAY)


@router.websocket("/events/ws")
async def agent_event_websocket(websocket: WebSocket):
    """WebSocket alternative to SSE — same OPAR envelopes, query-token auth."""
    if not await _accept_authorized_websocket(websocket):
        return
    await _websocket_event_loop(websocket)
