"""Shared test fixtures."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from src.app import create_app
from src.config import GatewaySettings


@pytest.fixture
def test_settings():
    """Settings with test defaults."""
    return GatewaySettings(
        jwt_secret="test-secret-key-for-testing-only",
        wazuh_api_url="http://localhost:55000",
        wazuh_api_password="test-password",
        minio_access_key="test-access",
        minio_secret_key="test-secret",
        debug=True,
    )


@pytest.fixture
def app(test_settings, monkeypatch):
    """Create test app with mocked clients."""
    from src.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("NEXUS_GW_JWT_SECRET", test_settings.jwt_secret)
    monkeypatch.setenv("NEXUS_GW_WAZUH_API_URL", test_settings.wazuh_api_url)
    monkeypatch.setenv("NEXUS_GW_WAZUH_API_PASSWORD", test_settings.wazuh_api_password)
    monkeypatch.setenv("NEXUS_GW_MINIO_ACCESS_KEY", test_settings.minio_access_key)
    monkeypatch.setenv("NEXUS_GW_MINIO_SECRET_KEY", test_settings.minio_secret_key)
    get_settings.cache_clear()

    app = create_app()
    # Mock clients to avoid real connections
    app.state.wazuh_client = AsyncMock()
    app.state.minio_client = MagicMock()
    app.state.athena_client = AsyncMock()
    app.state.ai_inference_client = AsyncMock()
    return app


@pytest.fixture
async def client(app):
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def make_token(test_settings):
    """Helper to generate valid JWT tokens for testing."""
    import jwt
    from datetime import datetime, timezone, timedelta

    def _make(sub: str = "testuser", role: str = "analyst", expired: bool = False):
        now = datetime.now(timezone.utc)
        exp = now - timedelta(hours=1) if expired else now + timedelta(hours=8)
        payload = {"sub": sub, "role": role, "iat": now, "exp": exp}
        return jwt.encode(payload, test_settings.jwt_secret, algorithm="HS256")

    return _make
