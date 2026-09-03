"""WebSocket alternative to agent SSE (Day 18)."""
import asyncio

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


class _FiniteStream:
    def __init__(self, events: list[dict]):
        self._events = events

    async def get_event_stream(self):
        for event in self._events:
            yield event
        await asyncio.sleep(3600)

    async def close(self) -> None:
        return


class _FailingStream:
    async def get_event_stream(self):
        raise ConnectionError("athena down")
        yield  # async generator  # noqa: B901

    async def close(self) -> None:
        return


@pytest.fixture
def ws_app(app):
    app.state.athena_client = _FiniteStream(
        [
            {
                "id": "e1",
                "phase": "act",
                "timestamp": "2026-09-03T16:00:00Z",
                "target": "night-quire",
            }
        ]
    )
    return app


def test_websocket_streams_opar_envelope(ws_app, make_token):
    token = make_token()
    stream = _FiniteStream(
        [
            {
                "id": "e1",
                "phase": "act",
                "timestamp": "2026-09-03T16:00:00Z",
                "target": "night-quire",
            }
        ]
    )
    with TestClient(ws_app) as client:
        ws_app.state.athena_client = stream
        with client.websocket_connect(f"/api/v1/agents/events/ws?token={token}") as ws:
            msg = ws.receive_json()
    assert msg["event"] == "opar"
    assert msg["id"] == "e1"
    assert msg["data"]["phase"] == "act"
    assert msg["data"]["target"] == "night-quire"


def test_websocket_rejects_missing_token(ws_app):
    with TestClient(ws_app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/agents/events/ws"):
                pass


def test_websocket_rejects_invalid_token(ws_app):
    with TestClient(ws_app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/agents/events/ws?token=not-a-jwt"):
                pass


def test_websocket_upstream_error_envelope(app, make_token):
    token = make_token()
    with TestClient(app) as client:
        app.state.athena_client = _FailingStream()
        with client.websocket_connect(f"/api/v1/agents/events/ws?token={token}") as ws:
            msg = ws.receive_json()
    assert msg["event"] == "error"
    assert msg["data"]["code"] == "UPSTREAM_DISCONNECTED"
