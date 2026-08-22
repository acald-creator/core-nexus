"""CORS preflight and credentialed-request headers."""
import pytest


CONSOLE_ORIGIN = "http://localhost:5173"
BLOCKED_ORIGIN = "http://evil.example"


@pytest.mark.asyncio
async def test_preflight_returns_204_with_cors_headers(client):
    response = await client.options(
        "/api/v1/artifacts?category=skills",
        headers={
            "Origin": CONSOLE_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 204
    assert response.headers.get("access-control-allow-origin") == CONSOLE_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allow_headers
    assert "content-type" in allow_headers


@pytest.mark.asyncio
async def test_preflight_rejects_unknown_origin(client):
    response = await client.options(
        "/api/v1/artifacts?category=skills",
        headers={
            "Origin": BLOCKED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") != BLOCKED_ORIGIN


@pytest.mark.asyncio
async def test_unauthorized_get_still_includes_cors_headers(client):
    response = await client.get(
        "/api/v1/artifacts?category=skills",
        headers={"Origin": CONSOLE_ORIGIN},
    )
    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == CONSOLE_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"
